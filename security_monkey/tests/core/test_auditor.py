#     Copyright 2016 Bridgewater Associates
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
.. module: security_monkey.tests.core.test_auditor
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.watcher import ChangeItem
from security_monkey.datastore import Item, ItemAudit, Account, Technology, ItemRevision
from security_monkey.datastore import AccountType, ItemAuditScore, AccountPatternAuditScore
from security_monkey.auditor import Auditor

from mixer.backend.flask import mixer


class TestAuditor(Auditor):
    index = 'test_index'
    i_am_singular = "test auditor"

    def __init__(self, accounts=None, debug=False):
        super(TestAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_test(self, item):
        self.add_issue(score=10, issue="Test issue", item=item)

class AuditorTestCase(SecurityMonkeyTestCase):
    def test_save_issues(self):
        mixer.init_app(self.app)
        test_account = mixer.blend(Account, name='test_account')
        technology = mixer.blend(Technology, name='testtech')
        item = Item(region="us-west-2", name="testitem", technology=technology, account=test_account)
        revision = mixer.blend(ItemRevision, item=item, config={}, active=True)
        item.latest_revision_id = revision.id
        mixer.blend(ItemAudit, item=item, issue='test issue')

        auditor = Auditor(accounts=[test_account.name])
        auditor.index = technology.name
        auditor.i_am_singular = technology.name
        auditor.audit_all_objects()

        try:
            auditor.save_issues()
        except AttributeError as e:
            self.fail("Auditor.save_issues() raised AttributeError unexpectedly: {}".format(e.message))

    def test_link_to_support_item_issue(self):
        sub_item_id = 2
        issue_text = 'This is a test issue'
        issue_score = 10

        auditor = Auditor(accounts=['test_account'])
        item = ChangeItem(index='test_index',
                          account='test_account', name='item_name')
        sub_item = Item(id=sub_item_id, tech_id=1,
                        account_id=1, name='sub_item_name')
        sub_item.issues.append(ItemAudit(score=issue_score, issue=issue_text))
        auditor.link_to_support_item_issues(item, sub_item, issue_text)
        self.assertTrue(len(item.audit_issues) == 1)
        new_issue = item.audit_issues[0]
        self.assertTrue(new_issue.score == issue_score)
        self.assertTrue(new_issue.issue == issue_text)
        self.assertTrue(len(new_issue.sub_items) == 1)
        self.assertTrue(new_issue.sub_items[0] == sub_item)

    def test_link_to_support_item_issues(self):
        auditor = Auditor(accounts=['test_account'])
        sub_item_id = 2
        issue1_text = 'This is test issue1'
        issue2_text = 'This is test issue2'
        issue1_score = 10
        issue2_score = 5

        item = ChangeItem(index='test_index',
                          account='test_account', name='item_name')
        sub_item = Item(id=sub_item_id, tech_id=1,
                        account_id=1, name='sub_item_name')
        sub_item.issues.append(
            ItemAudit(score=issue1_score, issue=issue1_text))
        sub_item.issues.append(
            ItemAudit(score=issue2_score, issue=issue2_text))
        auditor.link_to_support_item_issues(item, sub_item, None, "TEST")
        self.assertTrue(len(item.audit_issues) == 1)
        new_issue = item.audit_issues[0]
        self.assertTrue(new_issue.score == issue1_score + issue2_score)
        self.assertTrue(new_issue.issue == "TEST")
        self.assertTrue(len(new_issue.sub_items) == 1)
        self.assertTrue(new_issue.sub_items[0] == sub_item)

    def test_audit_item(self):
        auditor = TestAuditor(accounts=['test_account'])
        item = ChangeItem(index='test_index',
                          account='test_account', name='item_name')

        self.assertEquals(len(item.audit_issues), 0)
        auditor.audit_these_objects([item])
        self.assertEquals(len(item.audit_issues), 1)
        self.assertEquals(item.audit_issues[0].issue, 'Test issue')
        self.assertEquals(item.audit_issues[0].score, 10)

    def test_audit_item_method_disabled(self):
        mixer.init_app(self.app)
        mixer.blend(ItemAuditScore, technology='test_index', method='check_test (TestAuditor)',
                    score=0, disabled=True)

        auditor = TestAuditor(accounts=['test_account'])
        item = ChangeItem(index='test_index',
                          account='test_account', name='item_name')

        self.assertEquals(len(item.audit_issues), 0)
        auditor.audit_these_objects([item])
        self.assertEquals(len(item.audit_issues), 0)

    def test_audit_item_method_score_override(self):
        mixer.init_app(self.app)
        mixer.blend(ItemAuditScore, technology='test_index', method='check_test (TestAuditor)',
                    score=5, disabled=False)
        test_account_type = mixer.blend(AccountType, name='AWS')
        test_account = mixer.blend(Account, name='test_account', account_type=test_account_type)

        item = ChangeItem(index='test_index',
                          account=test_account.name, name='item_name')

        auditor = TestAuditor(accounts=[test_account.name])
        self.assertEquals(len(item.audit_issues), 0)
        auditor.audit_these_objects([item])
        self.assertEquals(len(item.audit_issues), 1)
        self.assertEquals(item.audit_issues[0].issue, 'Test issue')
        self.assertEquals(item.audit_issues[0].score, 5)

    def test_audit_item_method_account_pattern_score_override(self):
        mixer.init_app(self.app)
        test_account_type = mixer.blend(AccountType, name='AWS')
        test_account = mixer.blend(Account, name='test_account', account_type=test_account_type)
        account_pattern_score = AccountPatternAuditScore(account_type=test_account_type.name,
                                                         account_field='name', account_pattern=test_account.name,
                                                         score=2)

        mixer.blend(ItemAuditScore, technology='test_index', method='check_test (TestAuditor)',
                    score=5, disabled=False, account_pattern_scores=[account_pattern_score])

        item = ChangeItem(index='test_index',
                          account=test_account.name, name='item_name')

        auditor = TestAuditor(accounts=[test_account.name])
        self.assertEquals(len(item.audit_issues), 0)
        auditor.audit_these_objects([item])
        self.assertEquals(len(item.audit_issues), 1)
        self.assertEquals(item.audit_issues[0].issue, 'Test issue')
        self.assertEquals(item.audit_issues[0].score, 2)
