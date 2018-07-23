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
.. moduleauthor:: Mike Grima <mgrima@netflix.com>

"""
from flask_wtf.csrf import CSRFProtect, CSRFError
from security_monkey.factories import setup_app

from flask import render_template
import os

# SM VERSION
__version__ = '1.1.3'

# Init_app-able things:
csrf = CSRFProtect()  # Flask-WTF CSRF Protection

app = setup_app()


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


# For ELB and/or Eureka
@app.route('/healthcheck')
def healthcheck():
    return 'ok'



@app.errorhandler(CSRFError)
def csrf_error(reason):
    app.logger.debug("CSRF ERROR: {}".format(reason))
    return render_template('csrf_error.json', reason=reason), 400



### Flask-Security ###
#from flask_security.core import Security
# from flask_security.datastore import SQLAlchemyUserDatastore
# user_datastore = SQLAlchemyUserDatastore(db, User, Role)
#security = Security(app, user_datastore)


# @security.send_mail_task
# def send_email(msg):
#     """
#     Overrides the Flask-Security/Flask-Mail integration
#     to send emails out via boto and ses.
#     """
#     common_send_email(subject=msg.subject, recipients=msg.recipients, html=msg.html)




# from flask_security.views import login, logout, register, confirm_email, reset_password, forgot_password, \
#     change_password, send_confirmation

# rbac.exempt(login)
# rbac.exempt(logout)
# rbac.exempt(register)
# rbac.exempt(confirm_email)
# rbac.exempt(send_confirmation)
# rbac.exempt(reset_password)
# rbac.exempt(forgot_password)
# rbac.exempt(change_password)
# rbac.exempt(healthcheck)

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
api.add_resource(Distinct, '/api/1/distinct/<string:key_id>')

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



# from .sso.header_auth import HeaderAuthExtension
# header_auth = HeaderAuthExtension()
# header_auth.init_app(app)


