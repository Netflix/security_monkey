#     Copyright 2017 Bridgewater Associates
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
.. module: security_monkey.common.audit_issue_cleanup
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""

from security_monkey.auditor import auditor_registry
from security_monkey.datastore import AuditorSettings, Account, Technology, Datastore
from security_monkey.watcher import ChangeItem
from security_monkey import app, db


existing_auditor_classes = {}
for key in auditor_registry:
    for auditor in auditor_registry[key]:
        existing_auditor_classes[auditor.__name__] = auditor


def clean_stale_issues():
    results = AuditorSettings.query.filter().all()
    for settings in results:
        if settings.auditor_class is None or settings.auditor_class not in existing_auditor_classes:
            app.logger.info("Cleaning up issues for removed auditor %s", settings.auditor_class)
            _delete_issues(settings)

    db.session.commit()


def clean_account_issues(account):
    results = AuditorSettings.query.filter(AuditorSettings.account_id == account.id).all()
    for settings in results:
        auditor_class = existing_auditor_classes.get(settings.auditor_class)
        if auditor_class:
            if not auditor_class([account.name]).applies_to_account(account):
                app.logger.info("Cleaning up %s issues for %s", settings.auditor_class, account.name)
                _delete_issues(settings)

    db.session.commit()


def _delete_issues(settings):
    account = Account.query.filter(Account.id == settings.account_id).first()
    tech = Technology.query.filter(Technology.id == settings.tech_id).first()
    if account and tech:
        # Report issues as fixed
        db_items = Datastore().get_all_ctype_filtered(tech=tech.name, account=account.name, include_inactive=False)
        items = []
        for item in db_items:
            new_item = ChangeItem(index=tech.name,
                                  region=item.region,
                                  account=account.name,
                                  name=item.name,
                                  arn=item.arn)
            new_item.audit_issues = []
            new_item.db_item = item
            items.append(new_item)

        for item in items:
            for issue in item.db_item.issues:
                if issue.auditor_setting_id == settings.id:
                    item.confirmed_fixed_issues.append(issue)

    db.session.delete(settings)
