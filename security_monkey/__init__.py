#     Copyright 2014 Netflix, Inc.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
"""
.. module: security_monkey
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <patrick@netflix.com>

"""
### FLASK ###
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
app = Flask(__name__)
app.config.from_envvar("SECURITY_MONKEY_SETTINGS")
db = SQLAlchemy(app)


### LOGGING ###
import logging
from logging import Formatter
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
handler = RotatingFileHandler(app.config.get('LOG_FILE'), maxBytes=10000000, backupCount=100)
handler.setFormatter(
    Formatter('%(asctime)s %(levelname)s: %(message)s '
              '[in %(pathname)s:%(lineno)d]'
            ))
handler.setLevel(app.config.get('LOG_LEVEL'))
app.logger.setLevel(app.config.get('LOG_LEVEL'))
app.logger.addHandler(handler)
app.logger.addHandler(StreamHandler())


### Flask-Login ###
from flask.ext.login import LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

from security_monkey.datastore import User, Role


@login_manager.user_loader
def load_user(email):
    """
    For Flask-Login, returns the user object given the userid.
    :return: security_monkey.datastore.User object
    """
    app.logger.info("Inside load_user!")
    user = User.query.filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.session.add(user)
        db.session.commit()
        db.session.close()
        user = User.query.filter(User.email == email).first()
    return user


### Flask-Security ###
from flask.ext.security import Security, SQLAlchemyUserDatastore
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


### Flask Mail ###
from flask_mail import Mail
mail = Mail(app=app)
from security_monkey.common.utils.utils import send_email as common_send_email

@security.send_mail_task
def send_email(msg):
    """
    Overrides the Flask-Security/Flask-Mail integration
    to send emails out via boto and ses.
    """
    common_send_email(subject=msg.subject, recipients=msg.recipients, html=msg.html)


### FLASK API ###
from flask.ext.restful import Api
api = Api(app)

from security_monkey.views import ItemList, ItemGet, RevisionList
from security_monkey.views import Distinct, Logout, UserSettings
from security_monkey.views import Justify, RevisionComment, RevisionGet
from security_monkey.views import ItemCommentView, ItemAuditList, ItemAuditGet
from security_monkey.views import AccountGet, AccountList, AccountPost


# Get items, optionally filtered by region, account, name, ctype, or id
# Item is returned with latest revision
api.add_resource(ItemList, '/api/1/items/')
api.add_resource(ItemGet, '/api/1/item/<int:item_id>')
api.add_resource(ItemCommentView, '/api/1/comment/item/')

# Get recent revisions, optionally filtered by active, or id,
# account, region, or technology
api.add_resource(RevisionList, '/api/1/revisions/')
api.add_resource(RevisionGet, '/api/1/revision/<int:revision_id>')
api.add_resource(RevisionComment, '/api/1/comment/revision/')

# Get regions, accounts, names, accounts
api.add_resource(Distinct,    '/api/1/distinct/<string:key_id>')

# End the Flask-Logins session
api.add_resource(Logout, '/api/1/logout')

# User Settings
api.add_resource(UserSettings, '/api/1/settings')

# Item Justification
api.add_resource(Justify, '/api/1/justify/<string:audit_id>')

# Issue
api.add_resource(ItemAuditList, '/api/1/issues/')
api.add_resource(ItemAuditGet, '/api/1/issue/<int:audit_id>')

# Account
api.add_resource(AccountList, '/api/1/accounts/')
api.add_resource(AccountGet, '/api/1/account/<int:account_id>')
api.add_resource(AccountPost, '/api/1/account')


from security_monkey.watchers.sns import SNS, SNSItem
from security_monkey.auditors.sns import SNSAuditor
from security_monkey.watchers.sqs import SQS
from security_monkey.watchers.keypair import Keypair
from security_monkey.watchers.iam_role import IAMRole
from security_monkey.watchers.iam_group import IAMGroup
from security_monkey.watchers.iam_user import IAMUser, IAMUserItem
from security_monkey.auditors.iam_user import IAMUserAuditor
from security_monkey.watchers.security_group import SecurityGroup, SecurityGroupItem
from security_monkey.auditors.security_group import SecurityGroupAuditor
from security_monkey.watchers.rds_security_group import RDSSecurityGroup, RDSSecurityGroupItem
from security_monkey.auditors.rds_security_group import RDSSecurityGroupAuditor
from security_monkey.watchers.s3 import S3, S3Item
from security_monkey.auditors.s3 import S3Auditor
from security_monkey.watchers.elb import ELB
from security_monkey.watchers.iam_ssl import IAMSSL
from security_monkey.reporter import Reporter
from security_monkey.datastore import Account


def __prep_accounts__(accounts):
    if accounts == 'all':
        accounts = Account.query.filter(Account.third_party==False).filter(Account.active==True).all()
        accounts = [account.name for account in accounts]
        return accounts
    else:
        return accounts.split(',')


def run_change_reporter(accounts):
    """ Runs Reporter """
    accounts = __prep_accounts__(accounts)
    reporter = Reporter(accounts=accounts, alert_accounts=accounts, debug=True)
    for account in accounts:
        reporter.run(account)


def find_sqs_changes(accounts):
    """ Runs watchers/sqs"""
    accounts = __prep_accounts__(accounts)
    cw = SQS(accounts=accounts, debug=True)
    (items, exception_map) = cw.slurp()
    cw.find_changes(current=items, exception_map=exception_map)
    # SQS has no Audit rules to run.
    cw.save()
    db.session.close()


def find_elb_changes(accounts):
    """ Runs watchers/elb"""
    accounts = __prep_accounts__(accounts)
    cw = ELB(accounts=accounts, debug=True)
    (items, exception_map) = cw.slurp()
    cw.find_changes(current=items, exception_map=exception_map)
    # ELB has no Audit rules to run.
    cw.save()
    db.session.close()


def find_iamssl_changes(accounts):
    """ Runs watchers/iam_ssl"""
    accounts = __prep_accounts__(accounts)
    cw = IAMSSL(accounts=accounts, debug=True)
    (items, exception_map) = cw.slurp()
    cw.find_changes(current=items, exception_map=exception_map)
    # IAM SSL has no Audit rules to run.
    cw.save()
    db.session.close()


def find_rds_changes(accounts):
    """ Runs watchers/rds_security_group"""
    accounts = __prep_accounts__(accounts)
    cw = RDSSecurityGroup(accounts=accounts, debug=True)
    (items, exception_map) = cw.slurp()
    cw.find_changes(current=items, exception_map=exception_map)

    # Audit these changed items
    items_to_audit = []
    for item in cw.created_items + cw.changed_items:
        rds_item = RDSSecurityGroupItem(region=item.region, account=item.account, name=item.name, config=item.new_config)
        items_to_audit.append(rds_item)

    au = RDSSecurityGroupAuditor(accounts=accounts, debug=True)
    au.audit_these_objects(items_to_audit)
    au.save_issues()
    cw.save()
    db.session.close()


def audit_rds(accounts, send_report):
    """ Runs auditors/rds_security_group """
    accounts = __prep_accounts__(accounts)
    au = RDSSecurityGroupAuditor(accounts=accounts, debug=True)
    au.audit_all_objects()

    if send_report:
        report = au.create_report()
        au.email_report(report)

    au.save_issues()
    db.session.close()


def find_sg_changes(accounts):
    """ Runs watchers/security_group"""
    accounts = __prep_accounts__(accounts)
    cw = SecurityGroup(accounts=accounts, debug=True)
    (items, exception_map) = cw.slurp()
    cw.find_changes(current=items, exception_map=exception_map)

    # Audit these changed items
    items_to_audit = []
    for item in cw.created_items + cw.changed_items:
        sgitem = SecurityGroupItem(region=item.region, account=item.account, name=item.name, config=item.new_config)
        items_to_audit.append(sgitem)

    au = SecurityGroupAuditor(accounts=accounts, debug=True)
    au.audit_these_objects(items_to_audit)
    au.save_issues()

    cw.save()
    db.session.close()


def audit_sg(accounts, send_report):
    """ Runs auditors/security_group """
    accounts = __prep_accounts__(accounts)
    au = SecurityGroupAuditor(accounts=accounts, debug=True)
    au.audit_all_objects()

    if send_report:
        report = au.create_report()
        au.email_report(report)

    au.save_issues()
    db.session.close()


def find_s3_changes(accounts):
    """ Runs watchers/s3"""
    accounts = __prep_accounts__(accounts)
    cw = S3(accounts=accounts, debug=True)
    (items, exception_map) = cw.slurp()
    cw.find_changes(current=items, exception_map=exception_map)

    # Audit these changed items
    items_to_audit = []
    for item in cw.created_items + cw.changed_items:
        s3_item = S3Item(region=item.region, account=item.account, name=item.name, config=item.new_config)
        items_to_audit.append(s3_item)

    au = S3Auditor(accounts=accounts, debug=True)
    au.audit_these_objects(items_to_audit)
    au.save_issues()

    cw.save()
    db.session.close()


def audit_s3(accounts, send_report):
    """ Runs auditors/s3 """
    accounts = __prep_accounts__(accounts)
    au = S3Auditor(accounts=accounts, debug=True)
    au.audit_all_objects()

    if send_report:
        report = au.create_report()
        au.email_report(report)

    au.save_issues()
    db.session.close()


def find_iamuser_changes(accounts):
    """ Runs watchers/iamuser"""
    accounts = __prep_accounts__(accounts)
    cw = IAMUser(accounts=accounts, debug=True)
    (items, exception_map) = cw.slurp()
    cw.find_changes(current=items, exception_map=exception_map)

    # Audit these changed items
    items_to_audit = []
    for item in cw.created_items + cw.changed_items:
        iamuser_item = IAMUserItem(account=item.account, name=item.name, config=item.new_config)
        items_to_audit.append(iamuser_item)

    au = IAMUserAuditor(accounts=accounts, debug=True)
    au.audit_these_objects(items_to_audit)
    au.save_issues()

    cw.save()
    db.session.close()


def audit_iamuser(accounts, send_report):
    """ Runs auditors/iam_user """
    accounts = __prep_accounts__(accounts)
    au = IAMUserAuditor(accounts=accounts, debug=True)
    au.audit_all_objects()

    if send_report:
        report = au.create_report()
        au.email_report(report)

    au.save_issues()
    db.session.close()


def find_iamgroup_changes(accounts):
    """ Runs watchers/iamgroup"""
    accounts = __prep_accounts__(accounts)
    cw = IAMGroup(accounts=accounts, debug=True)
    (items, exception_map) = cw.slurp()
    cw.find_changes(current=items, exception_map=exception_map)

    # IAMGroup has no Audit rules to run.

    cw.save()
    db.session.close()


def find_iamrole_changes(accounts):
    """ Runs watchers/iamrole"""
    accounts = __prep_accounts__(accounts)
    cw = IAMRole(accounts=accounts, debug=True)
    (items, exception_map) = cw.slurp()
    cw.find_changes(current=items, exception_map=exception_map)

    # IAMRole has no Audit rules to run.

    cw.save()
    db.session.close()


def find_keypair_changes(accounts):
    """ Runs watchers/keypair"""
    accounts = __prep_accounts__(accounts)
    cw = Keypair(accounts=accounts, debug=True)
    (items, exception_map) = cw.slurp()
    cw.find_changes(current=items, exception_map=exception_map)

    # Keypair has no Audit rules to run.

    cw.save()
    db.session.close()


def find_sns_changes(accounts):
    """ Runs watchers/sns """
    accounts = __prep_accounts__(accounts)
    cw = SNS(accounts=accounts, debug=True)
    (items, exception_map) = cw.slurp()
    cw.find_changes(current=items, exception_map=exception_map)

    # Audit these changed items
    items_to_audit = []
    for item in cw.created_items + cw.changed_items:
        snsitem = SNSItem(region=item.region, account=item.account, name=item.name, config=item.new_config)
        items_to_audit.append(snsitem)

    au = SNSAuditor(accounts=accounts, debug=True)
    au.audit_these_objects(items_to_audit)
    au.save_issues()

    cw.save()
    db.session.close()


def audit_sns(accounts, send_report):
    """ Runs auditors/sns """
    accounts = __prep_accounts__(accounts)
    au = SNSAuditor(accounts=accounts, debug=True)
    au.audit_all_objects()

    if send_report:
        report = au.create_report()
        au.email_report(report)

    au.save_issues()
    db.session.close()


def run_account(account):
    """
    This should be refactored into Reporter.
    Runs the watchers/auditors for each account.
    Does not run the alerter.
    Times the operations and logs those results.
    """
    app.logger.info("Starting work on account {}.".format(account))
    time1 = time.time()
    find_sqs_changes(account)
    app.logger.info("Account {} is done with SQS".format(account))
    find_elb_changes(account)
    app.logger.info("Account {} is done with ELB".format(account))
    find_iamssl_changes(account)
    app.logger.info("Account {} is done with IAMSSL".format(account))
    find_rds_changes(account)
    app.logger.info("Account {} is done with RDS".format(account))
    find_sg_changes(account)
    app.logger.info("Account {} is done with SG".format(account))
    find_s3_changes(account)
    app.logger.info("Account {} is done with S3".format(account))
    find_iamuser_changes(account)
    app.logger.info("Account {} is done with IAMUSER".format(account))
    find_iamgroup_changes(account)
    app.logger.info("Account {} is done with IAMGROUP".format(account))
    find_iamrole_changes(account)
    app.logger.info("Account {} is done with IAMROLE".format(account))
    find_keypair_changes(account)
    app.logger.info("Account {} is done with KEYPAIR".format(account))
    find_sns_changes(account)
    app.logger.info("Account {} is done with SNS".format(account))
    time2 = time.time()
    app.logger.info('Run Account %s took %0.1f s' % (account, (time2-time1)))

from apscheduler.threadpool import ThreadPool
from apscheduler.scheduler import Scheduler
import traceback
import time
pool = ThreadPool(core_threads=25, max_threads=30, keepalive=0)
scheduler = Scheduler(standalone=True, threadpool=pool, coalesce=True, misfire_grace_time=30)
interval = 15


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
            #scheduler.add_interval_job(run_account, minutes=interval, args=[account])
            scheduler.add_interval_job(run_change_reporter, minutes=interval, args=[account])

            # Auditors
            scheduler.add_cron_job(audit_iamuser, hour=10, day_of_week="mon-fri", args=[account, True])
            scheduler.add_cron_job(audit_rds, hour=10, day_of_week="mon-fri", args=[account, True])
            scheduler.add_cron_job(audit_s3, hour=10, day_of_week="mon-fri", args=[account, True])
            scheduler.add_cron_job(audit_sg, hour=10, day_of_week="mon-fri", args=[account, True])
            scheduler.add_cron_job(audit_sns, hour=10, day_of_week="mon-fri", args=[account, True])
    except Exception as e:
        app.logger.warn("Scheduler Exception: {}".format(e))
        app.logger.warn(traceback.format_exc())
