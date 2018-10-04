#     Copyright 2018 Netflix, Inc.
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
.. moduleauthor:: Mike Grima <mgrima@netflix.com>
.. moduleauthor:: Patrick Kelley <patrick@netflix.com>

"""
from security_monkey.log import setup_base_logging
setup_base_logging()    # Must be first thing!

from security_monkey.factories import setup_app

# Blueprints:
from security_monkey.auth.views import mod as auth
from security_monkey.export import export_blueprint
from security_monkey.views.account import mod as account
from security_monkey.views.distinct import mod as distinct
from security_monkey.views.ignore_list import mod as ignore_list
from security_monkey.views.item import mod as items
from security_monkey.views.item_comment import mod as item_comment
from security_monkey.views.item_issue import mod as issues
from security_monkey.views.logout import mod as logout
from security_monkey.views.revision import mod as revisions
from security_monkey.views.user_settings import mod as settings
from security_monkey.views.users import mod as users
from security_monkey.views.whitelist import mod as whitelist
from security_monkey.views.auditor_settings import mod as auditor_settings
from security_monkey.views.audit_scores import mod as audit_scores
from security_monkey.views.tech_methods import mod as tech_methods
from security_monkey.views.account_pattern_audit_score import mod as account_pattern_audit_score
from security_monkey.views.watcher_config import mod as watcher_config
from security_monkey.views.healthcheck import mod as healthcheck

# SM VERSION
__version__ = '2.0'

BLUEPRINTS = [
    export_blueprint,
    auth,
    account,
    distinct,
    ignore_list,
    items,
    item_comment,
    issues,
    logout,
    revisions,
    settings,
    users,
    whitelist,
    auditor_settings,
    audit_scores,
    tech_methods,
    account_pattern_audit_score,
    watcher_config,
    healthcheck
]

app = setup_app(BLUEPRINTS)

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

# from .sso.header_auth import HeaderAuthExtension
# header_auth = HeaderAuthExtension()
# header_auth.init_app(app)

