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
.. module: security_monkey.tests.auditors.rds.test_rds_db_instance
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey import AWS_DEFAULT_REGION, ARN_PREFIX


class RDSDBInstanceTestCase(SecurityMonkeyTestCase):

    def test_check_internet_accessible(self):
        from security_monkey.auditors.rds.rds_db_instance import RDSDBInstanceAuditor
        auditor = RDSDBInstanceAuditor(accounts=['012345678912'])

        rds_instance = {
            'publicly_accessible': True,
            'vpc_security_groups': [
                {
                    'VpcSecurityGroupId': 'sg-12345678'
                }
            ],
            'endpoint': {
                'Port': 3306
            }
        }

        from security_monkey.watchers.rds.rds_db_instance import RDSDBInstanceItem
        item = RDSDBInstanceItem(
            account='TEST_ACCOUNT',
            name='MyRDSDbInstance', 
            arn=ARN_PREFIX + ":rds:" + AWS_DEFAULT_REGION + ":012345678910:db/MyDBInstance",
            config=rds_instance)

        def mock_get_auditor_support_items(*args, **kwargs):
            class MockIngressIssue:
                issue = 'Internet Accessible'
                notes = 'Entity: [cidr:0.0.0.0/0] Access: [ingress:tcp:3306]'
                score = 10

            class DBItem:
                issues = list()

            from security_monkey.watchers.security_group import SecurityGroupItem
            sg_item = SecurityGroupItem(
                region=AWS_DEFAULT_REGION,
                account='TEST_ACCOUNT',
                name='INTERNETSG',
                config={
                    'id': 'sg-12345678',
                    'name': 'INTERNETSG',
                    'rules': [
                        {
                            'cidr_ip': '0.0.0.0/0',
                            'rule_type': 'ingress',
                            'port': 3306
                        }
                    ]
                })

            sg_item.db_item = DBItem()
            sg_item.db_item.issues = [MockIngressIssue()]
            return [sg_item]

        def mock_link_to_support_item_issues(item, sg, sub_issue_message, score):
            auditor.add_issue(score, sub_issue_message, item, notes='Related to: INTERNETSG (sg-12345678 in vpc-49999999)')

        auditor.get_auditor_support_items = mock_get_auditor_support_items
        auditor.link_to_support_item_issues = mock_link_to_support_item_issues
        auditor.check_internet_accessible(item)

        self.assertEqual(len(item.audit_issues), 1)
        issue = item.audit_issues[0]
        self.assertEqual(issue.issue, 'Internet Accessible')
        self.assertEqual(issue.notes, 'Related to: INTERNETSG (sg-12345678 in vpc-49999999)')

