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


# For ELB and/or Eureka
@app.route('/healthcheck')
def healthcheck():
    return 'ok'

### LOGGING ###
import logging
from logging import Formatter
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
handler = RotatingFileHandler(app.config.get('LOG_FILE'), maxBytes=10000000, backupCount=100)
handler.setFormatter(
    Formatter('%(asctime)s %(levelname)s: %(message)s '
              '[in %(pathname)s:%(lineno)d]')
)
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

from security_monkey.views.account import AccountGetPutDelete
from security_monkey.views.account import AccountPostList
api.add_resource(AccountGetPutDelete, '/api/1/accounts/<int:account_id>')
api.add_resource(AccountPostList, '/api/1/accounts')

from security_monkey.views.distinct import Distinct
api.add_resource(Distinct,    '/api/1/distinct/<string:key_id>')

from security_monkey.views.ignore_list import IgnoreListGetPutDelete
from security_monkey.views.ignore_list import IgnorelistListPost
api.add_resource(IgnoreListGetPutDelete, '/api/1/ignorelistentries/<int:item_id>')
api.add_resource(IgnorelistListPost, '/api/1/ignorelistentries')

from security_monkey.views.item import ItemList
from security_monkey.views.item import ItemGet
api.add_resource(ItemList, '/api/1/items')
api.add_resource(ItemGet, '/api/1/items/<int:item_id>')

from security_monkey.views.item_comment import ItemCommentPost
from security_monkey.views.item_comment import ItemCommentDelete
from security_monkey.views.item_comment import ItemCommentGet
api.add_resource(ItemCommentPost, '/api/1/items/<int:item_id>/comments')
api.add_resource(ItemCommentDelete, '/api/1/items/<int:item_id>/comments/<int:comment_id>')
api.add_resource(ItemCommentGet, '/api/1/items/<int:item_id>/comments/<int:comment_id>')

from security_monkey.views.item_issue import ItemAuditGet
from security_monkey.views.item_issue import ItemAuditList
api.add_resource(ItemAuditList, '/api/1/issues')
api.add_resource(ItemAuditGet, '/api/1/issues/<int:audit_id>')

from security_monkey.views.item_issue_justification import JustifyPostDelete
api.add_resource(JustifyPostDelete, '/api/1/issues/<int:audit_id>/justification')

from security_monkey.views.logout import Logout
api.add_resource(Logout, '/api/1/logout')

from security_monkey.views.revision import RevisionList
from security_monkey.views.revision import RevisionGet
api.add_resource(RevisionList, '/api/1/revisions')
api.add_resource(RevisionGet, '/api/1/revisions/<int:revision_id>')

from security_monkey.views.revision_comment import RevisionCommentPost
from security_monkey.views.revision_comment import RevisionCommentGet
from security_monkey.views.revision_comment import RevisionCommentDelete
api.add_resource(RevisionCommentPost, '/api/1/revisions/<int:revision_id>/comments')
api.add_resource(RevisionCommentGet, '/api/1/revisions/<int:revision_id>/comments/<int:comment_id>')
api.add_resource(RevisionCommentDelete, '/api/1/revisions/<int:revision_id>/comments/<int:comment_id>')

from security_monkey.views.user_settings import UserSettings
api.add_resource(UserSettings, '/api/1/settings')

from security_monkey.views.whitelist import WhitelistGetPutDelete
from security_monkey.views.whitelist import WhitelistListPost
api.add_resource(WhitelistGetPutDelete, '/api/1/whitelistcidrs/<int:item_id>')
api.add_resource(WhitelistListPost, '/api/1/whitelistcidrs')


from security_monkey.watchers.sns import SNS, SNSItem
from security_monkey.auditors.sns import SNSAuditor
from security_monkey.watchers.sqs import SQS
from security_monkey.watchers.keypair import Keypair
from security_monkey.watchers.iam_role import IAMRole, IAMRoleItem
from security_monkey.auditors.iam_role import IAMRoleAuditor
from security_monkey.watchers.iam_group import IAMGroup, IAMGroupItem
from security_monkey.auditors.iam_group import IAMGroupAuditor
from security_monkey.watchers.iam_user import IAMUser, IAMUserItem
from security_monkey.auditors.iam_user import IAMUserAuditor
from security_monkey.watchers.security_group import SecurityGroup, SecurityGroupItem
from security_monkey.auditors.security_group import SecurityGroupAuditor
from security_monkey.watchers.rds_security_group import RDSSecurityGroup, RDSSecurityGroupItem
from security_monkey.auditors.rds_security_group import RDSSecurityGroupAuditor
from security_monkey.watchers.s3 import S3, S3Item
from security_monkey.auditors.s3 import S3Auditor
from security_monkey.watchers.elb import ELB, ELBItem
from security_monkey.auditors.elb import ELBAuditor
from security_monkey.watchers.iam_ssl import IAMSSL
from security_monkey.watchers.redshift import Redshift, RedshiftCluster
from security_monkey.auditors.redshift import RedshiftAuditor
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

def find_changes(accounts, watcher_class, auditor_class=None, item_class=None, debug=True):
    """ Runs a watcher and auditor on changed items """
    accounts = __prep_accounts__(accounts)
    cw = watcher_class(accounts=accounts, debug=True)
    (items, exception_map) = cw.slurp()
    cw.find_changes(current=items, exception_map=exception_map)

    # Audit these changed items
    if auditor_class and item_class:
        items_to_audit = []
        for item in cw.created_items + cw.changed_items:
            cluster = item_class(region=item.region, account=item.account, name=item.name, config=item.new_config)
            items_to_audit.append(cluster)

        au = auditor_class(accounts=accounts, debug=True)
        au.audit_these_objects(items_to_audit)
        au.save_issues()

    cw.save()
    db.session.close()

def audit_changes(accounts, send_report, auditor_class, debug=True):
    """ Runs an auditors on all items """
    accounts = __prep_accounts__(accounts)
    au = auditor_class(accounts=accounts, debug=True)
    au.audit_all_objects()

    if send_report:
        report = au.create_report()
        au.email_report(report)

    au.save_issues()
    db.session.close()

def find_sqs_changes(accounts):
    """ Runs watchers/sqs"""
    find_changes(accounts, SQS, debug=True)

def find_elb_changes(accounts):
    """ Runs watchers/elb"""
    find_changes(accounts, ELB, ELBAuditor, ELBItem, debug=True)

def audit_elb(accounts, send_report):
    """ Runs auditors/elb """
    audit_changes(accounts, send_report, ELBAuditor, debug=True)

def find_iamssl_changes(accounts):
    """ Runs watchers/iam_ssl"""
    find_changes(accounts, IAMSSL, debug=True)

def find_rds_changes(accounts):
    """ Runs watchers/rds_security_group"""
    find_changes(accounts, RDSSecurityGroup, RDSSecurityGroupAuditor, RDSSecurityGroupItem, debug=True)

def audit_rds(accounts, send_report):
    """ Runs auditors/rds_security_group """
    audit_changes(accounts, send_report, RDSSecurityGroupAuditor, debug=True)

def find_sg_changes(accounts):
    """ Runs watchers/security_group"""
    find_changes(accounts, SecurityGroup, SecurityGroupAuditor, SecurityGroupItem, debug=True)

def audit_sg(accounts, send_report):
    """ Runs auditors/security_group """
    audit_changes(accounts, send_report, SecurityGroupAuditor, debug=True)

def find_s3_changes(accounts):
    """ Runs watchers/s3"""
    find_changes(accounts, S3, S3Auditor, S3Item, debug=True)

def audit_s3(accounts, send_report):
    """ Runs auditors/s3 """
    audit_changes(accounts, send_report, S3Auditor, debug=True)

def find_iamuser_changes(accounts):
    """ Runs watchers/iamuser"""
    find_changes(accounts, IAMUser, IAMUserAuditor, IAMUserItem, debug=True)

def audit_iamuser(accounts, send_report):
    """ Runs auditors/iam_user """
    audit_changes(accounts, send_report, IAMUserAuditor, debug=True)

def audit_iamrole(accounts, send_report):
    """ Runs auditors/iam_role """
    audit_changes(accounts, send_report, IAMRoleAuditor, debug=True)

def audit_iamgroup(accounts, send_report):
    """ Runs auditors/iam_group """
    audit_changes(accounts, send_report, IAMGroupAuditor, debug=True)

def find_iamgroup_changes(accounts):
    """ Runs watchers/iamgroup"""
    find_changes(accounts, IAMGroup, IAMGroupAuditor, IAMGroupItem, debug=True)

def find_iamrole_changes(accounts):
    """ Runs watchers/iamrole"""
    find_changes(accounts, IAMRole, IAMRoleAuditor, IAMRoleItem, debug=True)

def find_keypair_changes(accounts):
    """ Runs watchers/keypair"""
    find_changes(accounts, Keypair, debug=True)

def find_sns_changes(accounts):
    """ Runs watchers/sns """
    find_changes(accounts, SNS, SNSAuditor, SNSItem, debug=True)

def audit_sns(accounts, send_report):
    """ Runs auditors/sns """
    audit_changes(accounts, send_report, SNSAuditor, debug=True)

def find_redshift_changes(accounts):
    """ Runs watchers/redshift """
    find_changes(accounts, Redshift, RedshiftAuditor, RedshiftCluster, debug=True)

def audit_redshift(accounts, send_report):
    """ Runs auditors/redshift """
    audit_changes(accounts, send_report, RedshiftAuditor, debug=True)

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
    find_redshift_changes(account)
    app.logger.info("Account {} is done with Redshift".format(account))
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
