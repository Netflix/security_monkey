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
from security_monkey import db
from security_monkey.datastore import Account, AccountType
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.auditors.kms import KMSAuditor
from security_monkey.watchers.kms import KMSMasterKey
from security_monkey import AWS_DEFAULT_REGION, ARN_PREFIX
from copy import deepcopy


# Internet Accessible
# No Condition
# rotation Enabled
key0 = {
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
  "KeyRotationEnabled": True,
  "CreationDate": "2017-01-05T20:39:18.960000+00:00",
  "Arn": ARN_PREFIX + ":kms:" + AWS_DEFAULT_REGION + ":123456789123:key/key_id",
  "AWSAccountId": "123456789123"
}

# Access provided to role in same account
# Rotation Not Enabled
key1 = {
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
            "AWS": "arn:aws:iam::123456789123:role/SuperRole"
          }
        }
      ]
    }
  ],
  "KeyState": "Enabled",
  "KeyRotationEnabled": False,
  "CreationDate": "2017-01-05T20:39:18.960000+00:00",
  "Arn": ARN_PREFIX + ":kms:" + AWS_DEFAULT_REGION + ":123456789123:key/key_id",
  "AWSAccountId": "123456789123"
}


class KMSTestCase(SecurityMonkeyTestCase):

    def pre_test_setup(self):
        KMSAuditor(accounts=['TEST_ACCOUNT']).OBJECT_STORE.clear()
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

    def test_check_internet_accessible(self):
        auditor = KMSAuditor(accounts=['TEST_ACCOUNT'])

        # Make sure it detects an internet accessible policy
        item = KMSMasterKey(
            arn=ARN_PREFIX + ':kms:' + AWS_DEFAULT_REGION + ':123456789123:key/key_id',
            config=key0)
        auditor.check_internet_accessible(item)

        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].score, 10)

        # Copy of key0, but not internet accessible
        key0_fixed = deepcopy(key0)
        key0_fixed['Policies'][0]['Statement'][0]['Principal']['AWS'] \
            = 'arn:aws:iam::123456789123:role/SomeRole'
        item = KMSMasterKey(
            arn='arn:aws:kms:us-east-1:123456789123:key/key_id',
            config=key0_fixed)
        auditor.check_internet_accessible(item)
        self.assertEqual(len(item.audit_issues), 0)

    def test_check_friendly_cross_account(self):
        auditor = KMSAuditor(accounts=['TEST_ACCOUNT'])
        auditor.prep_for_audit()

        key0_friendly_cross_account = deepcopy(key0)
        key0_friendly_cross_account['Policies'][0]['Statement'][0]['Principal']['AWS'] \
            = 'arn:aws:iam::222222222222:role/SomeRole'
        item = KMSMasterKey(
            account='TEST_ACCOUNT',
            arn='arn:aws:kms:us-east-1:123456789123:key/key_id',
            config=key0_friendly_cross_account)
        auditor.check_friendly_cross_account(item)
        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].score, 0)

    def test_check_thirdparty_cross_account(self):
        auditor = KMSAuditor(accounts=['TEST_ACCOUNT'])
        auditor.prep_for_audit()

        key0_friendly_cross_account = deepcopy(key0)
        key0_friendly_cross_account['Policies'][0]['Statement'][0]['Principal']['AWS'] \
            = 'arn:aws:iam::333333333333:role/SomeRole'
        item = KMSMasterKey(
            account='TEST_ACCOUNT',
            arn='arn:aws:kms:us-east-1:123456789123:key/key_id',
            config=key0_friendly_cross_account)
        auditor.check_thirdparty_cross_account(item)
        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].score, 0)

    def test_check_unknown_cross_account(self):
        auditor = KMSAuditor(accounts=['TEST_ACCOUNT'])
        auditor.prep_for_audit()

        key0_friendly_cross_account = deepcopy(key0)
        key0_friendly_cross_account['Policies'][0]['Statement'][0]['Principal']['AWS'] \
            = 'arn:aws:iam::444444444444:role/SomeRole'
        item = KMSMasterKey(
            account='TEST_ACCOUNT',
            arn='arn:aws:kms:us-east-1:123456789123:key/key_id',
            config=key0_friendly_cross_account)
        auditor.check_unknown_cross_account(item)
        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].score, 10)

    def test_check_root_cross_account(self):
        auditor = KMSAuditor(accounts=['TEST_ACCOUNT'])
        auditor.prep_for_audit()

        key0_friendly_cross_account = deepcopy(key0)
        key0_friendly_cross_account['Policies'][0]['Statement'][0]['Principal']['AWS'] \
            = 'arn:aws:iam::222222222222:root'
        item = KMSMasterKey(
            account='TEST_ACCOUNT',
            arn='arn:aws:kms:us-east-1:123456789123:key/key_id',
            config=key0_friendly_cross_account)
        auditor.check_root_cross_account(item)
        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].score, 6)

    def test_check_for_kms_key_rotation(self):
        auditor = KMSAuditor(accounts=['unittestaccount'])
        item = KMSMasterKey(arn=ARN_PREFIX + ':kms:' + AWS_DEFAULT_REGION + ':123456789123:key/key_id',
                            config=key0)

        auditor.check_for_kms_key_rotation(item)
        self.assertEqual(len(item.audit_issues), 0)

        item = KMSMasterKey(arn='arn:aws:kms:us-east-1:123456789123:key/key_id',
                            config=key1)

        auditor.check_for_kms_key_rotation(item)

        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].score, 1)
