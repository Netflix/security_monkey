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
from collections import defaultdict

from security_monkey import db
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.watcher import ChangeItem
from security_monkey.datastore import Item, ItemAudit, Account, Technology, ItemRevision
from security_monkey.datastore import AccountType, ItemAuditScore, AccountPatternAuditScore
from security_monkey.auditor import Auditor


class AuditorTestObj(Auditor):
    index = 'test_index'
    i_am_singular = "test auditor"

    def __init__(self, accounts=None, debug=False):
        super(AuditorTestObj, self).__init__(accounts=accounts, debug=debug)

    def check_test(self, item):
        self.add_issue(score=10, issue="Test issue", item=item)


class AuditorTestCase(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        self.account_type = AccountType.query.filter(AccountType.name == 'AWS').first()
        if not self.account_type:
            self.account_type = AccountType(name='AWS')
            db.session.add(self.account_type)
            db.session.commit()
        self.test_account = Account(type=self.account_type, name="test_account", identifier="012345678910")
        self.technology = Technology(name="testtech")

        db.session.add(self.test_account)
        db.session.add(self.technology)
        db.session.commit()

    def tearDown(self):
        import security_monkey.auditor
        security_monkey.auditor.auditor_registry = defaultdict(list)
        super(AuditorTestCase, self).tearDown()

    def test_save_issues(self):
        item = Item(region="us-west-2", name="testitem", technology=self.technology, account=self.test_account)
        revision = ItemRevision(item=item, config={}, active=True)
        item_audit = ItemAudit(item=item, issue="test issue")
        db.session.add(item)
        db.session.add(revision)
        db.session.add(item_audit)
        db.session.commit()

        auditor = Auditor(accounts=[self.test_account.name])
        auditor.index = self.technology.name
        auditor.i_am_singular = self.technology.name
        auditor.items = auditor.read_previous_items()
        auditor.audit_objects()

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

        item = ChangeItem(index='test_index', account='test_account', name='item_name')
        sub_item = Item(id=sub_item_id, tech_id=1, account_id=1, name='sub_item_name')
        sub_item.issues.append(ItemAudit(score=issue1_score, issue=issue1_text))
        sub_item.issues.append(ItemAudit(score=issue2_score, issue=issue2_text))

        auditor.link_to_support_item_issues(item, sub_item, issue_message="TEST")
        self.assertTrue(len(item.audit_issues) == 1)
        new_issue = item.audit_issues[0]

        self.assertTrue(new_issue.score == issue1_score + issue2_score)
        self.assertTrue(new_issue.issue == "TEST")
        self.assertTrue(len(new_issue.sub_items) == 1)
        self.assertTrue(new_issue.sub_items[0] == sub_item)

    def test_audit_item(self):
        auditor = AuditorTestObj(accounts=['test_account'])
        item = ChangeItem(index='test_index',
                          account='test_account', name='item_name')

        self.assertEqual(len(item.audit_issues), 0)
        auditor.items = [item]
        auditor.audit_objects()
        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].issue, 'Test issue')
        self.assertEqual(item.audit_issues[0].score, 10)

    def test_audit_item_method_disabled(self):
        item_audit_score = ItemAuditScore(technology='test_index', method='check_test (AuditorTestObj)',
                                          score=0, disabled=True)
        db.session.add(item_audit_score)
        db.session.commit()

        auditor = AuditorTestObj(accounts=['test_account'])
        item = ChangeItem(index='test_index',
                          account='test_account', name='item_name')

        self.assertEqual(len(item.audit_issues), 0)
        auditor.items = [item]
        auditor.audit_objects()
        self.assertEqual(len(item.audit_issues), 0)

    def test_audit_item_method_score_override(self):
        item_audit_score = ItemAuditScore(technology='test_index', method='check_test (AuditorTestObj)',
                                          score=5, disabled=False)
        db.session.add(item_audit_score)
        db.session.commit()

        item = ChangeItem(index='test_index',
                          account=self.test_account.name, name='item_name')

        auditor = AuditorTestObj(accounts=[self.test_account.name])
        self.assertEqual(len(item.audit_issues), 0)
        auditor.items = [item]
        auditor.audit_objects()
        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].issue, 'Test issue')
        self.assertEqual(item.audit_issues[0].score, 5)

    def test_audit_item_method_account_pattern_score_override(self):
        account_pattern_score = AccountPatternAuditScore(account_type=self.account_type.name,
                                                         account_field='name', account_pattern=self.test_account.name,
                                                         score=2)

        item_audit_score = ItemAuditScore(technology='test_index', method='check_test (AuditorTestObj)',
                                          score=5, disabled=False, account_pattern_scores=[account_pattern_score])
        db.session.add(account_pattern_score)
        db.session.add(item_audit_score)
        db.session.commit()

        item = ChangeItem(index='test_index',
                          account=self.test_account.name, name='item_name')

        auditor = AuditorTestObj(accounts=[self.test_account.name])
        self.assertEqual(len(item.audit_issues), 0)
        auditor.items = [item]
        auditor.audit_objects()
        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].issue, 'Test issue')
        self.assertEqual(item.audit_issues[0].score, 2)

    def test_issue_presevation(self):
        """
        Ensure that issues are not deleted and that justifications are preserved.
            new issue
            existing issue
            fixed issue
            regressed issue
        Context: PR 788
        """
        auditor = AuditorTestObj(accounts=['test_account'])
        item = ChangeItem(index='test_index',
                          account='test_account', name='item_name')

        self.assertEqual(len(item.audit_issues), 0)
        auditor.items = [item]

        # New Issue
        auditor.audit_objects()
        self.assertEqual(len(item.audit_issues), 1)
        auditor.save_issues()
        self.assertEqual(item.audit_issues[0].fixed, False)
        self.assertEqual(item.audit_issues[0].justified, False)

        issue = item.audit_issues[0]

        # Justify this new issue.
        from security_monkey import db
        for issue in ItemAudit.query.all():
            issue.justified = True
            issue.justification = 'This is okay because...'
            db.session.add(issue)
        db.session.commit()

        # Existing Issue
        auditor.audit_objects()
        self.assertEqual(len(item.audit_issues), 1)
        auditor.save_issues()
        self.assertEqual(item.audit_issues[0].fixed, False)
        self.assertEqual(item.audit_issues[0].justified, True)

        # Fixed Issue
        item.audit_issues = []
        auditor.save_issues()
        self.assertEqual(issue.fixed, True)
        self.assertEqual(issue.justified, True)

        # Regressed Issue
        auditor.audit_objects()
        auditor.save_issues()
        self.assertEqual(issue.fixed, False)
        self.assertEqual(issue.justified, True)
