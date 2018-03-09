#     Copyright 2017 Google, Inc.
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

"""
.. module: security_monkey.tests.auditors.gcp.iam.test_serviceaccount
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Tom Melendez <supertom@google.com> @supertom
"""

POLICY_WITH_ACTOR_LIST = [
    {
        "Members": [
            "user:test-user@gmail.com"
        ],
        "Role": "roles/iam.serviceAccountActor"
    }
]


POLICY_NO_ACTOR_LIST = [
    {
        "Members": [
            "user:test-user@gmail.com"
        ],
        "Role": "roles/viewer"
    }
]


class IAMServiceAccountTestCase(SecurityMonkeyTestCase):
    def test__max_keys(self):
        from security_monkey.auditors.gcp.iam.serviceaccount import IAMServiceAccountAuditor
        auditor = IAMServiceAccountAuditor(accounts=['unittest'])
        # NOTE: the config value below actually controls this so ensure
        # it is set to 1
        auditor.gcp_config.MAX_SERVICEACCOUNT_KEYS = 1
        actual = auditor._max_keys(2)
        self.assertTrue(isinstance(actual, list))

        actual = auditor._max_keys(1)
        self.assertFalse(actual)

    def test__actor_role(self):
        from security_monkey.auditors.gcp.iam.serviceaccount import IAMServiceAccountAuditor
        auditor = IAMServiceAccountAuditor(accounts=['unittest'])
        # NOTE: the config value below actually controls this so ensure
        # it is set to 1
        auditor.gcp_config.MAX_SERVICEACCOUNT_KEYS = 1
        actual = auditor._actor_role(POLICY_WITH_ACTOR_LIST)
        self.assertTrue(isinstance(actual, list))

        actual = auditor._actor_role(POLICY_NO_ACTOR_LIST)
        self.assertFalse(actual)
