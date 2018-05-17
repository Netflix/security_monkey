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
.. module: security_monkey.tests.core.test_audit_issue_cleanup
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.auditor import Auditor
from security_monkey.datastore import Account, AccountType, Technology
from security_monkey.datastore import Item, ItemAudit, AuditorSettings
from security_monkey.auditor import auditor_registry
from security_monkey import db, app, ARN_PREFIX

from mock import patch
from collections import defaultdict


class MockAuditor(Auditor):
    def __init__(self, accounts=None, debug=False):
        super(MockAuditor, self).__init__(accounts=accounts, debug=debug)



    def applies_to_account(self, account):
        return self.applies


test_auditor_registry = defaultdict(list)


auditor_configs = [
    {
        'type': 'MockAuditor1',
        'index': 'index1',
        'applies': True
    },
    {
        'type': 'MockAuditor2',
        'index': 'index2',
        'applies': False
    },
]

for config in auditor_configs:
    auditor = type(
                config['type'], (MockAuditor,),
                {
                    'applies': config['applies']
                }
            )
    app.logger.debug(auditor.__name__)

    test_auditor_registry[config['index']].append(auditor)


class AuditIssueCleanupTestCase(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        account_type_result = AccountType.query.filter(AccountType.name == 'AWS').first()
        if not account_type_result:
            account_type_result = AccountType(name='AWS')
            db.session.add(account_type_result)
            db.session.commit()

        self.account = Account(identifier="012345678910", name="testing",
                               account_type_id=account_type_result.id)

        self.technology = Technology(name="iamrole")
        item = Item(region="us-west-2", name="testrole",
                    arn=ARN_PREFIX + ":iam::012345678910:role/testrole", technology=self.technology,
                    account=self.account)

        db.session.add(self.account)
        db.session.add(self.technology)
        db.session.add(item)
        db.session.commit()

    def tearDown(self):
        import security_monkey.auditor
        security_monkey.auditor.auditor_registry = defaultdict(list)
        super(AuditIssueCleanupTestCase, self).tearDown()

    @patch.dict(auditor_registry, test_auditor_registry, clear=True)
    def test_clean_stale_issues(self):
        from security_monkey.common.audit_issue_cleanup import clean_stale_issues

        items = Item.query.all()
        assert len(items) == 1
        item = items[0]
        item.issues.append(ItemAudit(score=1, issue='Test Issue', item_id=item.id,
                                     auditor_setting=AuditorSettings(disabled=False,
                                                                     technology=self.technology,
                                                                     account=self.account,
                                                                     auditor_class='MockAuditor1')))

        item.issues.append(ItemAudit(score=1, issue='Issue with missing auditor', item_id=item.id,
                                     auditor_setting=AuditorSettings(disabled=False,
                                                                     technology=self.technology,
                                                                     account=self.account,
                                                                     auditor_class='MissingAuditor')))

        db.session.commit()

        clean_stale_issues()
        items = Item.query.all()
        assert len(items) == 1
        item = items[0]
        assert len(item.issues) == 1
        assert item.issues[0].issue == 'Test Issue'

    @patch.dict(auditor_registry, test_auditor_registry, clear=True)
    def test_clean_account_issues(self):
        from security_monkey.common.audit_issue_cleanup import clean_account_issues

        items = Item.query.all()
        assert len(items) == 1
        item = items[0]

        item.issues.append(ItemAudit(score=1, issue='Test Issue 1', item_id=item.id,
                                     auditor_setting=AuditorSettings(disabled=False,
                                                                     technology=self.technology,
                                                                     account=self.account,
                                                                     auditor_class='MockAuditor1')))

        item.issues.append(ItemAudit(score=1, issue='Test Issue 2', item_id=item.id,
                                     auditor_setting=AuditorSettings(disabled=False,
                                                                     technology=self.technology,
                                                                     account=self.account,
                                                                     auditor_class='MockAuditor2')))

        db.session.commit()

        clean_account_issues(self.account)
        items = Item.query.all()
        assert len(items) == 1
        item = items[0]
        assert len(item.issues) == 1
        assert item.issues[0].issue == 'Test Issue 1'
