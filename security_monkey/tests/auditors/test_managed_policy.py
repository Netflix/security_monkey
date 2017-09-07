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
.. module: security_monkey.tests.auditors.test_managed_policy
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>

"""
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.auditors.iam.managed_policy import ManagedPolicyAuditor
from security_monkey.watchers.iam.managed_policy import ManagedPolicyItem
from security_monkey import ARN_PREFIX


FULL_ADMIN_POLICY_BARE = """
{
    "Statement":    {
        "Effect": "Allow",
        "Action": "*"
    }
}
"""


class ManagedPolicyAuditorTestCase(SecurityMonkeyTestCase):

    def test_issue_on_non_aws_policy(self):
        import json

        config = {
            'policy': json.loads(FULL_ADMIN_POLICY_BARE),
            'arn': ARN_PREFIX + ':iam::123456789:policy/TEST',
            'attached_users': [],
            'attached_roles': [],
            'attached_groups': []
        }

        auditor = ManagedPolicyAuditor(accounts=['unittest'])
        policyobj = ManagedPolicyItem(account="TEST_ACCOUNT", name="policy_test", config=config)

        self.assertIs(len(policyobj.audit_issues), 0,
                      "Managed Policy should have 0 alert but has {}".format(len(policyobj.audit_issues)))

        auditor.check_star_privileges(policyobj)
        self.assertIs(len(policyobj.audit_issues), 1,
                      "Managed Policy should have 1 alert but has {}".format(len(policyobj.audit_issues)))

    def test_issue_on_aws_policy_no_attachments(self):
        import json

        config = {
            'policy': json.loads(FULL_ADMIN_POLICY_BARE),
            'arn': ARN_PREFIX + ':iam::aws:policy/TEST',
            'attached_users': [],
            'attached_roles': [],
            'attached_groups': []
        }

        auditor = ManagedPolicyAuditor(accounts=['unittest'])
        policyobj = ManagedPolicyItem(account="TEST_ACCOUNT", name="policy_test", config=config)

        self.assertIs(len(policyobj.audit_issues), 0,
                      "Managed Policy should have 0 alert but has {}".format(len(policyobj.audit_issues)))

        auditor.check_star_privileges(policyobj)
        self.assertIs(len(policyobj.audit_issues), 0,
                      "Managed Policy should have 0 alerts but has {}".format(len(policyobj.audit_issues)))

    def test_issue_on_aws_policy_with_attachment(self):
        import json

        config = {
            'policy': json.loads(FULL_ADMIN_POLICY_BARE),
            'arn': ARN_PREFIX + ':iam::aws:policy/TEST',
            'attached_users': [],
            'attached_roles': [ARN_PREFIX + ':iam::123456789:role/TEST'],
            'attached_groups': []
        }

        auditor = ManagedPolicyAuditor(accounts=['unittest'])
        policyobj = ManagedPolicyItem(account="TEST_ACCOUNT", name="policy_test", config=config)

        self.assertIs(len(policyobj.audit_issues), 0,
                      "Managed Policy should have 0 alert but has {}".format(len(policyobj.audit_issues)))

        auditor.check_star_privileges(policyobj)
        self.assertIs(len(policyobj.audit_issues), 1,
                      "Managed Policy should have 1 alert but has {}".format(len(policyobj.audit_issues)))
