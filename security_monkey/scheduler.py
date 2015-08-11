"""
.. module: security_monkey.scheduler
    :platform: Unix
    :synopsis: Runs watchers, auditors, or reports on demand or on a schedule

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

from apscheduler.threadpool import ThreadPool
from apscheduler.scheduler import Scheduler

from security_monkey.datastore import Account
from security_monkey.parse import parse_tech_names, parse_accounts
from security_monkey.reporter import Reporter

from security_monkey import app, db, handler, jirasync, watcher, auditor

import traceback
import logging
from datetime import datetime, timedelta


def run_change_reporter(accounts, interval=None):
    """ Runs Reporter """
    accounts = parse_accounts(accounts)
    reporter = Reporter(accounts=accounts, alert_accounts=accounts, debug=True)
    for account in accounts:
        reporter.run(account, interval)


def find_changes(accounts, tech_names, debug=True):
    tech_names = parse_tech_names(tech_names)
    for tech_name in tech_names:
        watcher_class = watcher.watcher_registry[tech_name]
        auditor_classes = auditor.auditor_registry[tech_name]
        _find_changes(accounts, watcher_class, auditor_classes, debug)


def audit_changes(accounts, tech_names, send_report, debug=True):
    tech_names = parse_tech_names(tech_names)
    accounts = parse_accounts(accounts)
    auditors = []
    for tech_name in tech_names:
        auditor_classes = auditor.auditor_registry[tech_name]
        for auditor_class in auditor_classes:
            auditors.append(auditor_class(accounts=accounts, debug=True))
    if auditors:
        _audit_changes(accounts, auditors, send_report, debug)


def _find_changes(accounts, watcher_class, auditor_classes, debug=True):
    """ Runs a watcher and auditor on changed items """
    accounts = parse_accounts(accounts)
    cw = watcher_class(accounts=accounts, debug=True)
    (items, exception_map) = cw.slurp()
    cw.find_changes(current=items, exception_map=exception_map)

    # Audit these changed items
    items_to_audit = [item for item in cw.created_items + cw.changed_items]
    for auditor_class in auditor_classes:
        au = auditor_class(accounts=accounts, debug=True)
        au.audit_these_objects(items_to_audit)
        au.save_issues()

    cw.save()
    db.session.close()


def _audit_changes(accounts, auditors, send_report, debug=True):
    """ Runs auditors on all items """
    for au in auditors:
        au.audit_all_objects()
        if send_report:
            report = au.create_report()
            au.email_report(report)
        au.save_issues()

        if jirasync:
            app.logger.info('Syncing {} issues on {} with Jira'.format(au.index, accounts))
            jirasync.sync_issues(accounts, au.index)


pool = ThreadPool(
    core_threads=app.config.get('CORE_THREADS', 25),
    max_threads=app.config.get('MAX_THREADS', 30),
    keepalive=0
)
scheduler = Scheduler(
    standalone=True,
    threadpool=pool,
    coalesce=True,
    misfire_grace_time=30
)


def setup_scheduler():
    """Sets up the APScheduler"""
    log = logging.getLogger('apscheduler')
    log.setLevel(app.config.get('LOG_LEVEL'))
    log.addHandler(handler)

    try:
        accounts = Account.query.filter(Account.third_party==False).filter(Account.active==True).all()
        accounts = [account.name for account in accounts]
        for account in accounts:
            print "Scheduler adding account {}".format(account)
            rep = Reporter(accounts=[account])
            for period in rep.get_intervals(account):
                scheduler.add_interval_job(
                    run_change_reporter,
                    minutes=period,
                    start_date=datetime.now()+timedelta(seconds=2),
                    args=[account, period]
                )
            auditors = [a for (_, a) in rep.get_watchauditors(account) if a]
            if auditors:
                scheduler.add_cron_job(_audit_changes, hour=10, day_of_week="mon-fri", args=[account, auditors, True])

    except Exception as e:
        app.logger.warn("Scheduler Exception: {}".format(e))
        app.logger.warn(traceback.format_exc())
