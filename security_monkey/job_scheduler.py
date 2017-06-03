from security_monkey.datastore import JobRun, JobType
from security_monkey.datastore import Account
from security_monkey.datastore import Technology
from security_monkey import app, db
import requests


NOT_COMPLETED_STATES = frozenset(['QUEUED', 'STARTING', 'RUNNING'])
COMPLETED_STATES = frozenset(['FINISHED', 'FAILED', 'CRASHED', 'STOPPED'])


def update_status(job):
    """
    Ask Titus for the status of a given NOT_COMPLETE job.
    Update our job status table.

    TODO:
    Alert if a job is taking abnormally long.
        - Is Titus starving us out? (Long time in QUEUED/STARTING)
        - Is our job taking twice as long as it normally does? (Long time in RUNNING)
    Alert if a job fails repeatedly.

    :param job: JobRun object
    :return: None
    """
    status_url = app.config.get('JOB_STATUS').format(job_id=job.job_id)
    resp = requests.get(status_url).json()
    job.status = resp['tasks'][0]['state']
    job.job_type.status = resp['tasks'][0]['state']
    if job.status in COMPLETED_STATES:
        from dateutil import parser
        dt = parser.parse(resp['tasks'][0]['finishedAt'])
        job.date_completed = dt
    db.session.add(job)
    db.session.commit()


def get_jobs(accounts, monitors, enabled=True):
    return JobType.query.join((Account, Account.id == JobType.account_id)) \
        .join((Technology, Technology.id == JobType.tech_id)) \
        .filter(Account.name.in_(accounts)) \
        .filter(Technology.name.in_(monitors)) \
        .filter(JobType.enabled == enabled).all()


def get_unfinished_jobs(accounts, monitors, enabled=True):
    return JobRun.query.join((JobType, JobRun.job_type_id == JobType.id)) \
        .join((Account, Account.id == JobType.account_id)) \
        .join((Technology, Technology.id == JobType.tech_id)) \
        .filter(JobType.enabled == enabled) \
        .filter(Account.name.in_(accounts)) \
        .filter(Technology.name.in_(monitors)) \
        .filter(JobRun.status.notin_(COMPLETED_STATES)).all()


def update_job_status_tracking_db(accounts, monitors):
    """
    For each outstanding job, query to obtain current status.
    :param accounts: list of account names
    :param monitors: list of technology names
    :return: None
    """
    jobs = get_unfinished_jobs(accounts, monitors)
    print('Updating status on existing {} jobs...'.format(len(jobs)))
    for job in jobs:
        print('Updating status on job with id {}'.format(job.job_id))
        update_status(job)


def kill_job(job):
    """
    POST to the Titus endpoint to kill the specified job.
    :param job: instance of JobRun
    :return: None
    """
    print('Killing job {}'.format(str(job)))
    job_args = dict(
        jobId=job.job_id,
        user='manage.py manual kill'
    )
    post_url = app.config.get('JOB_KILL')
    resp = requests.post(post_url, json=job_args)

    job.status = 'STOPPED'
    job.job_type.status = 'STOPPED'
    db.session.add(job)
    db.session.commit()



def post_job(account, technology):
    """
    Post a watcher job to Titus.
    :param account: Account object
    :param technology: Technology object
    :return: Titus Job ID (str)
    """
    job_args = dict(
        name="security_monkey {account}, {technology}".format(account=account.name, technology=technology.name),
        # applicationName="securitymonkey",
        applicationName="examples/helloworld",
        instances="1",
        cpu="1",
        memory="256",
        # entryPoint="/apps/python/bin/python /apps/securitymonkey/manage.py find_changes -a {account} -m {technology}".format(account=account.name, technology=technology.name),
        entryPoint="cat hello.txt",
        disk="10",
        version="0.0.0.1"
    )

    import json
    print('POSTING JOB TO TITUS {}'.format(json.dumps(job_args)))

    post_url = app.config.get('JOB_POST')
    resp = requests.post(post_url, json=job_args).json()

    # {"jobUri":"/v2/jobs/Titus-15609"}
    return resp['jobUri'].split('/')[-1]


def _create_tech(technology_name):
    """
    Creates an entry in the Technology table.
    :param technology_name:  Cloud technology like ses/iamuser
    :return:  technology object
    """
    technology = Technology(name=technology_name)
    db.session.add(technology)
    db.session.commit()
    db.session.refresh(technology)
    app.logger.info("Creating a new Technology: {} - ID: {}"
                    .format(technology_name, technology.id))
    return technology


def post_jobs_to_job_runner(accounts, monitors):
    """
    Find jobs to submit to Titus.
    Do not launch a job if the previous run has not completed.
    :param accounts: list of account names
    :param monitors: list of technology names
    """
    import itertools

    for account, technology_name in itertools.product(accounts, monitors):
        if technology_name != 'ses':
            continue
        print('post jobs account:{} tech:{}'.format(account, technology_name))
        account = Account.query.filter(Account.name == account).one()
        technology = Technology.query.filter(Technology.name == technology_name).first()
        if not technology:
            technology = _create_tech(technology_name)

        job_type = JobType.query.filter(JobType.account_id == account.id) \
            .filter(JobType.tech_id == technology.id).first()

        if job_type and job_type.status not in COMPLETED_STATES:
            print('Skipping {jt} because status {status}'.format(jt=job_type, status=job_type.status))
            continue

        if not job_type:
            print('Creating JobType {a}:{t}'.format(a=account.name, t=technology.name))
            job_type = JobType(account_id=account.id,tech_id=technology.id)
            db.session.add(job_type)
            db.session.commit()
            db.session.refresh(job_type)

        job_id = post_job(account, technology)
        job_run = JobRun(job_id=job_id, job_type_id=job_type.id, status='QUEUED')
        job_type.status = 'QUEUED'
        db.session.add(job_run)
        db.session.add(job_type)
        db.session.commit()