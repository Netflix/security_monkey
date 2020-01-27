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
"""
.. module: security_monkey.tests.auditors.gcp.gcs.test_bucket
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Tom Melendez <supertom@google.com> @supertom
"""
from security_monkey.tests import SecurityMonkeyTestCase

ACL_LIST = [
    {'role': 'OWNER', 'entity': 'project-editors-2094195755359'},
    {'role': 'READER', 'entity': 'project-viewers-2094195755359'},
    {'role': 'WRITER', 'entity': 'project-writer-2094195755359'}
]

ACL_LIST_TWO_OWNERS = [
    {'role': 'OWNER', 'entity': 'project-editors-2094195755359'},
    {'role': 'READER', 'entity': 'project-viewers-2094195755359'},
    {'role': 'OWNER', 'entity': 'project-editors-2094195755359'}
]

ACL_LIST_ALLUSERS = [
    {'role': 'OWNER', 'entity': 'project-editors-2094195755359'},
    {'role': 'READER', 'entity': 'allUsers'},
    {'role': 'OWNER', 'entity': 'project-editors-2094195755359'}
]


class BucketTestCase(SecurityMonkeyTestCase):
    def test__acl_allusers_exists(self):
        from security_monkey.auditors.gcp.gcs.bucket import GCSBucketAuditor
        auditor = GCSBucketAuditor(accounts=['unittest'])

        actual = auditor._acl_allusers_exists(ACL_LIST)
        self.assertFalse(actual)
        actual = auditor._acl_allusers_exists(ACL_LIST_ALLUSERS)
        self.assertTrue(actual)
        
    def test__acl_max_owners(self):
        from security_monkey.auditors.gcp.gcs.bucket import GCSBucketAuditor
        auditor = GCSBucketAuditor(accounts=['unittest'])

        # NOTE: the config value below actually controls this so ensure
        # it is set to 1
        auditor.gcp_config.MAX_OWNERS_PER_BUCKET = 1
        actual = auditor._acl_max_owners(ACL_LIST)
        self.assertFalse(actual)
        actual = auditor._acl_max_owners(ACL_LIST_TWO_OWNERS)
        self.assertTrue(actual)
