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
import os
import stat

### VERSION ###
__version__ = '1.1.1'

### FLASK ###
from flask import Flask
from flask import render_template
from flask.helpers import make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os


app = Flask(__name__, static_url_path='/static')

# If SECURITY_MONKEY_SETTINGS is set, then use that.
# Otherwise, use env-config/config.py
if os.environ.get('SECURITY_MONKEY_SETTINGS'):
    app.config.from_envvar('SECURITY_MONKEY_SETTINGS')
else:
    # find env-config/config.py
    from os.path import dirname, join, isfile
    path = dirname(dirname(__file__))
    path = join(path, 'env-config')
    path = join(path, 'config.py')

    if isfile(path):
        app.config.from_pyfile(path)
    else:
        print('PLEASE SET A CONFIG FILE WITH SECURITY_MONKEY_SETTINGS OR PUT ONE AT env-config/config.py')
        exit(-1)

"""
Govcloud works in the following way.
If the AWS_GOVCLOUD configuration is set to True:
    the arn prefix is set to: arn:aws-us-gov:...
and the default region is set to: us-gov-west-1
else:
    the arn prefix is set to: arn:aws:...
and the default region is set to: us-east-1
"""
ARN_PARTITION = 'aws'
AWS_DEFAULT_REGION = 'us-east-1'

if app.config.get("AWS_GOVCLOUD"):
    ARN_PARTITION = 'aws-us-gov'
    AWS_DEFAULT_REGION = 'us-gov-west-1'

ARN_PREFIX = 'arn:' + ARN_PARTITION

db = SQLAlchemy(app)

# For ELB and/or Eureka
@app.route('/healthcheck')
def healthcheck():
    return 'ok'


### Flask Mail ###
from flask_mail import Mail
mail = Mail(app=app)
from security_monkey.common.utils import send_email as common_send_email

### Flask-WTF CSRF Protection ###
from flask_wtf.csrf import CSRFProtect, CSRFError

csrf = CSRFProtect()
csrf.init_app(app)


@app.errorhandler(CSRFError)
def csrf_error(reason):
    app.logger.debug("CSRF ERROR: {}".format(reason))
    return render_template('csrf_error.json', reason=reason), 400


from security_monkey.datastore import User, Role

### Flask-Security ###
from flask_security.core import Security
from flask_security.datastore import SQLAlchemyUserDatastore
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


@security.send_mail_task
def send_email(msg):
    """
    Overrides the Flask-Security/Flask-Mail integration
    to send emails out via boto and ses.
    """
    common_send_email(subject=msg.subject, recipients=msg.recipients, html=msg.html)

from .auth.modules import RBAC
rbac = RBAC(app=app)

from flask_security.views import login, logout, register, confirm_email, reset_password, forgot_password, \
    change_password, send_confirmation

rbac.exempt(login)
rbac.exempt(logout)
rbac.exempt(register)
rbac.exempt(confirm_email)
rbac.exempt(send_confirmation)
rbac.exempt(reset_password)
rbac.exempt(forgot_password)
rbac.exempt(change_password)
rbac.exempt(healthcheck)

### Sentry definition ###
sentry = None

### FLASK API ###
from flask_restful import Api
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

from security_monkey.views.users import UserList, Roles, UserDetail
api.add_resource(UserList, '/api/1/users')
api.add_resource(UserDetail, '/api/1/users/<int:user_id>')
api.add_resource(Roles, '/api/1/roles')

from security_monkey.views.whitelist import WhitelistGetPutDelete
from security_monkey.views.whitelist import WhitelistListPost
api.add_resource(WhitelistGetPutDelete, '/api/1/whitelistcidrs/<int:item_id>')
api.add_resource(WhitelistListPost, '/api/1/whitelistcidrs')

from security_monkey.views.auditor_settings import AuditorSettingsGet
from security_monkey.views.auditor_settings import AuditorSettingsPut
api.add_resource(AuditorSettingsGet, '/api/1/auditorsettings')
api.add_resource(AuditorSettingsPut, '/api/1/auditorsettings/<int:as_id>')

from security_monkey.views.account_config import AccountConfigGet
api.add_resource(AccountConfigGet, '/api/1/account_config/<string:account_fields>')

from security_monkey.views.audit_scores import AuditScoresGet
from security_monkey.views.audit_scores import AuditScoreGetPutDelete
api.add_resource(AuditScoresGet, '/api/1/auditscores')
api.add_resource(AuditScoreGetPutDelete, '/api/1/auditscores/<int:id>')

from security_monkey.views.tech_methods import TechMethodsGet
api.add_resource(TechMethodsGet, '/api/1/techmethods/<string:tech_ids>')

from security_monkey.views.account_pattern_audit_score import AccountPatternAuditScoreGet
from security_monkey.views.account_pattern_audit_score import AccountPatternAuditScorePost
from security_monkey.views.account_pattern_audit_score import AccountPatternAuditScoreGetPutDelete
api.add_resource(AccountPatternAuditScoreGet, '/api/1/auditscores/<int:auditscores_id>/accountpatternauditscores')
api.add_resource(AccountPatternAuditScorePost, '/api/1/accountpatternauditscores')
api.add_resource(AccountPatternAuditScoreGetPutDelete, '/api/1/accountpatternauditscores/<int:id>')


from security_monkey.views.account_bulk_update import AccountListPut
api.add_resource(AccountListPut, '/api/1/accounts_bulk/batch')

from security_monkey.views.watcher_config import WatcherConfigGetList
from security_monkey.views.watcher_config import WatcherConfigPut
api.add_resource(WatcherConfigGetList, '/api/1/watcher_config')
api.add_resource(WatcherConfigPut, '/api/1/watcher_config/<int:id>')

## Jira Sync
from security_monkey.jirasync import JiraSync
jirasync_file = os.environ.get('SECURITY_MONKEY_JIRA_SYNC')
if jirasync_file:
    try:
        jirasync = JiraSync(jirasync_file)
    except Exception as e:
        app.logger.error(repr(e))
        jirasync = None
else:
    jirasync = None

# Blueprints
from security_monkey.sso.views import mod as sso_bp
from security_monkey.export import export_blueprint
BLUEPRINTS = [sso_bp, export_blueprint]

for bp in BLUEPRINTS:
    app.register_blueprint(bp, url_prefix="/api/1")

# Logging
import sys
from logging import Formatter, handlers
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
from logging.config import dictConfig
from logging import DEBUG


# Use this handler to have log rotator give newly minted logfiles +gw perm
class GroupWriteRotatingFileHandler(handlers.RotatingFileHandler):
    def doRollover(self):
        """
        Override base class method to make the new log file group writable.
        """
        # Rotate the file first.
        handlers.RotatingFileHandler.doRollover(self)

        # Add group write to the current permissions.
        try:
            currMode = os.stat(self.baseFilename).st_mode
            os.chmod(self.baseFilename, currMode | stat.S_IWGRP)
        except OSError:
            pass


handlers.GroupWriteRotatingFileHandler = GroupWriteRotatingFileHandler


def setup_logging():
    """
    Logging in security_monkey can be configured in two ways.

    1) Vintage: Set LOG_FILE and LOG_LEVEL in your config.
    LOG_FILE will default to stderr if no value is supplied.
    LOG_LEVEL will default to DEBUG if no value is supplied.

        LOG_LEVEL = "DEBUG"
        LOG_FILE = "/var/log/security_monkey/securitymonkey.log"

    2) Set LOG_CFG in your config to a PEP-0391 compatible
    logging configuration.

        LOG_CFG = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s %(levelname)s: %(message)s '
                        '[in %(pathname)s:%(lineno)d]'
                }
            },
            'handlers': {
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'DEBUG',
                    'formatter': 'standard',
                    'filename': '/var/log/security_monkey/securitymonkey.log',
                    'maxBytes': 10485760,
                    'backupCount': 100,
                    'encoding': 'utf8'
                },
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'DEBUG',
                    'formatter': 'standard',
                    'stream': 'ext://sys.stdout'
                }
            },
            'loggers': {
                'security_monkey': {
                    'handlers': ['file', 'console'],
                    'level': 'DEBUG'
                },
                'apscheduler': {
                    'handlers': ['file', 'console'],
                    'level': 'INFO'
                }
            }
        }
    """
    if not app.debug:
        if app.config.get('LOG_CFG'):
            # initialize the Flask logger (removes all handlers)
            _ = app.logger
            dictConfig(app.config.get('LOG_CFG'))
        else:
            # capability with previous config settings
            # Should have LOG_FILE and LOG_LEVEL set
            if app.config.get('LOG_FILE') is not None:
                handler = RotatingFileHandler(app.config.get('LOG_FILE'), maxBytes=10000000, backupCount=100)
            else:
                handler = StreamHandler(stream=sys.stderr)

            handler.setFormatter(
                Formatter('%(asctime)s %(levelname)s: %(message)s '
                          '[in %(pathname)s:%(lineno)d]')
            )
            app.logger.setLevel(app.config.get('LOG_LEVEL', DEBUG))
            app.logger.addHandler(handler)


setup_logging()


from .sso.header_auth import HeaderAuthExtension
header_auth = HeaderAuthExtension()
header_auth.init_app(app)


### Sentry ###
try:
    from raven.contrib.flask import Sentry
    sentry = Sentry()
    sentry.init_app(app)
except ImportError as e:
    app.logger.debug('Sentry not installed, skipping...')
