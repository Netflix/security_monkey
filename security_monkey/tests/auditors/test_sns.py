#     Copyright 2017 Netflix, Inc.
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
.. module: security_monkey.tests.auditors.sns
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.auditors.sns import SNSAuditor
from security_monkey.watchers.sns import SNSItem
from security_monkey.datastore import Account, AccountType
from security_monkey import db


class SNSAuditorTestCase(SecurityMonkeyTestCase):

    def pre_test_setup(self):
        SNSAuditor(accounts=['TEST_ACCOUNT']).OBJECT_STORE.clear()
        account_type_result = AccountType(name='AWS')
        db.session.add(account_type_result)
        db.session.commit()

        # main
        account = Account(identifier="123456789123", name="TEST_ACCOUNT",
                          account_type_id=account_type_result.id, notes="TEST_ACCOUNT",
                          third_party=False, active=True)
        # friendly
        account2 = Account(identifier="222222222222", name="TEST_ACCOUNT_TWO",
                          account_type_id=account_type_result.id, notes="TEST_ACCOUNT_TWO",
                          third_party=False, active=True)
        # third party
        account3 = Account(identifier="333333333333", name="TEST_ACCOUNT_THREE",
                          account_type_id=account_type_result.id, notes="TEST_ACCOUNT_THREE",
                          third_party=True, active=True)

        db.session.add(account)
        db.session.add(account2)
        db.session.add(account3)
        db.session.commit()

    def test_check_snstopicpolicy_empty(self):
        auditor = SNSAuditor(accounts=['TEST_ACCOUNT'])
        item = SNSItem(config=dict())
        auditor.check_snstopicpolicy_empty(item)

        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].score, 1)

    def test_check_subscriptions_crossaccount(self):
        auditor = SNSAuditor(accounts=['TEST_ACCOUNT'])
        auditor.prep_for_audit()

        # Unknown account ID
        item = SNSItem(config=dict(
            subscriptions=[{
                    "Owner": "020202020202",
                    "Endpoint": "someemail@example.com",
                    "Protocol": "email",
                    "TopicArn": "arn:aws:sns:us-east-1:020202020202:somesnstopic",
                    "SubscriptionArn": "arn:aws:sns:us-east-1:020202020202:somesnstopic:..."
                }]))
        auditor.check_subscriptions_crossaccount(item)
        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].score, 10)

        # Friendly account ID
        item = SNSItem(config=dict(
            subscriptions=[{
                    "Owner": "222222222222",
                    "Endpoint": "someemail@example.com",
                    "Protocol": "email",
                    "TopicArn": "arn:aws:sns:us-east-1:012345678910:somesnstopic",
                    "SubscriptionArn": "arn:aws:sns:us-east-1:012345678910:somesnstopic:..."
                }]))
        auditor.check_subscriptions_crossaccount(item)
        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].score, 0)

        # ThirdParty account ID
        item = SNSItem(config=dict(
            subscriptions=[{
                    "Owner": "333333333333",
                    "Endpoint": "someemail@example.com",
                    "Protocol": "email",
                    "TopicArn": "arn:aws:sns:us-east-1:012345678910:somesnstopic",
                    "SubscriptionArn": "arn:aws:sns:us-east-1:012345678910:somesnstopic:..."
                }]))
        auditor.check_subscriptions_crossaccount(item)
        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].score, 0)