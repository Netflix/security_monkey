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
.. module: security_monkey.tests.test_kms
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""

from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.auditors.kms import KMSAuditor
from security_monkey.watchers.kms import KMSMasterKey
from security_monkey import AWS_DEFAULT_REGION, ARN_PREFIX

key_no_condition = {
  "Origin": "AWS_KMS",
  "KeyId": "key_id",
  "Description": "Description",
  "Enabled": True,
  "KeyUsage": "ENCRYPT_DECRYPT",
  "Grants": [],
  "Policies": [
    {
      "Version": "2012-10-17",
      "Id": "key-consolepolicy-2",
      "Statement": [
        {
          "Action": "kms:*",
          "Sid": "Enable IAM User Permissions",
          "Resource": "*",
          "Effect": "Allow",
          "Principal": {
            "AWS": "*"
          }
        }
      ]
    }
  ],
  "KeyState": "Enabled",
  "CreationDate": "2017-01-05T20:39:18.960000+00:00",
  "Arn": ARN_PREFIX + ":kms:" + AWS_DEFAULT_REGION + ":123456789123:key/key_id",
  "AWSAccountId": "123456789123"
}

key_arn_is_role_id = {
  "Origin": "AWS_KMS",
  "KeyId": "key_id",
  "Description": "Description",
  "Enabled": True,
  "KeyUsage": "ENCRYPT_DECRYPT",
  "Grants": [],
  "Policies": [
    {
      "Version": "2012-10-17",
      "Id": "key-consolepolicy-2",
      "Statement": [
        {
          "Resource": "*",
          "Effect": "Allow",
          "Sid": "Allow attachment of persistent resources",
          "Action": [
            "kms:CreateGrant",
            "kms:ListGrants",
            "kms:RevokeGrant"
          ],
          "Condition": {
            "Bool": {
              "kms:GrantIsForAWSResource": "true"
            }
          },
          "Principal": {
            "AWS": "role_id_for_arn"
          }
        }
      ]
    }
  ],
  "KeyState": "Enabled",
  "CreationDate": "2017-01-05T20:39:18.960000+00:00",
  "Arn": ARN_PREFIX + ":kms:" + AWS_DEFAULT_REGION + ":123456789123:key/key_id",
  "AWSAccountId": "123456789123"
}


class KMSTestCase(SecurityMonkeyTestCase):

    def test_check_for_kms_policy_with_foreign_account_no_condition(self):
        auditor = KMSAuditor(accounts=['unittestaccount'])
        item = KMSMasterKey(arn=ARN_PREFIX + ':kms:' + AWS_DEFAULT_REGION + ':123456789123:key/key_id',
                            config=key_no_condition)

        self.assertEquals(len(item.audit_issues), 0)
        auditor.check_for_kms_policy_with_foreign_account(item)
        self.assertEquals(len(item.audit_issues), 1)

    def test_check_for_kms_policy_with_foreign_account_key_arn_is_role_id(self):
        auditor = KMSAuditor(accounts=['unittestaccount'])
        item = KMSMasterKey(arn=ARN_PREFIX + ':kms:' + AWS_DEFAULT_REGION + ':123456789123:key/key_id',
                            config=key_arn_is_role_id)

        self.assertEquals(len(item.audit_issues), 0)
        auditor.check_for_kms_policy_with_foreign_account(item)
        self.assertEquals(len(item.audit_issues), 0)
