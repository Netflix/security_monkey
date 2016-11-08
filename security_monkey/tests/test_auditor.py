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
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.watcher import ChangeItem
from security_monkey.datastore import Item, ItemAudit
from security_monkey.auditor import Auditor


class AuditorTestCase(SecurityMonkeyTestCase):

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
