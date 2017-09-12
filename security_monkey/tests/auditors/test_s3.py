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
.. module: security_monkey.tests.auditors.test_s3
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Mike Grima <mgrima@netflix.com>

"""
import json

from security_monkey.auditors.s3 import S3Auditor
from security_monkey.datastore import Account, AccountType, AccountTypeCustomValues
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey import db

from security_monkey.cloudaux_watcher import CloudAuxChangeItem

# With same account ownership:
CONFIG_ONE = json.loads(b"""{
      "Acceleration": null,
      "AnalyticsConfigurations": [],
      "Arn": "arn:aws:s3:::bucket1",
      "Cors": [],
      "GrantReferences": {
        "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389": "test_accnt1"
      },
      "Grants": {
        "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389": [
          "FULL_CONTROL"
        ]
      },
      "InventoryConfigurations": [],
      "LifecycleRules": [],
      "Logging": {},
      "MetricsConfigurations": [],
      "Notifications": {},
      "Owner": {
        "ID": "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389"
      },
      "Policy": null,
      "Region": "us-east-1",
      "Replication": {},
      "Tags": {
        "LOL": "UNITTESTS"
      },
      "Versioning": {},
      "Website": null,
      "_version": 5
    }
    """)

# ACL with unknown access:
CONFIG_TWO = json.loads(b"""{
      "Acceleration": null,
      "AnalyticsConfigurations": [],
      "Arn": "arn:aws:s3:::bucket2",
      "Cors": [],
      "GrantReferences": {
        "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389": "test_accnt1"
      },
      "Grants": {
        "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389": [
          "FULL_CONTROL"
        ],
        "34589673489752397023749287uiouwshjksdhfdjkshfdjkshf2381": [
          "FULL_CONTROL"
        ]
      },
      "InventoryConfigurations": [],
      "LifecycleRules": [],
      "Logging": {},
      "MetricsConfigurations": [],
      "Notifications": {},
      "Owner": {
        "ID": "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389"
      },
      "Policy": null,
      "Region": "us-east-1",
      "Replication": {},
      "Tags": {
        "LOL": "UNITTESTS"
      },
      "Versioning": {},
      "Website": null,
      "_version": 5
    }
    """)

# ACL with friendly access:
CONFIG_THREE = json.loads(b"""{
      "Acceleration": null,
      "AnalyticsConfigurations": [],
      "Arn": "arn:aws:s3:::bucket3",
      "Cors": [],
      "GrantReferences": {
        "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389": "test_accnt1",
        "lksdjfilou32890u47238974189237euhuu128937192837189uyh1hr3": "test_accnt2"
      },
      "Grants": {
        "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389": [
          "FULL_CONTROL"
        ],
        "lksdjfilou32890u47238974189237euhuu128937192837189uyh1hr3": [
          "FULL_CONTROL"
        ]
      },
      "InventoryConfigurations": [],
      "LifecycleRules": [],
      "Logging": {},
      "MetricsConfigurations": [],
      "Notifications": {},
      "Owner": {
        "ID": "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389"
      },
      "Policy": null,
      "Region": "us-east-1",
      "Replication": {},
      "Tags": {
        "LOL": "UNITTESTS"
      },
      "Versioning": {},
      "Website": null,
      "_version": 5
    }
    """)

# ACL with friendly 3rd party account access:
CONFIG_FOUR = json.loads(b"""{
      "Acceleration": null,
      "AnalyticsConfigurations": [],
      "Arn": "arn:aws:s3:::bucket4",
      "Cors": [],
      "GrantReferences": {
        "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389": "test_accnt1"
      },
      "Grants": {
        "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389": [
          "FULL_CONTROL"
        ],
        "dsfhgiouhy23984723789y4riuwhfkajshf91283742389u823723": [
          "FULL_CONTROL"
        ]
      },
      "InventoryConfigurations": [],
      "LifecycleRules": [],
      "Logging": {},
      "MetricsConfigurations": [],
      "Notifications": {},
      "Owner": {
        "ID": "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389"
      },
      "Policy": null,
      "Region": "us-east-1",
      "Replication": {},
      "Tags": {
        "LOL": "UNITTESTS"
      },
      "Versioning": {},
      "Website": null,
      "_version": 5
    }
    """)

# ACL with AllUsers:
CONFIG_FIVE = json.loads(b"""{
      "Acceleration": null,
      "AnalyticsConfigurations": [],
      "Arn": "arn:aws:s3:::bucket5",
      "Cors": [],
      "GrantReferences": {
        "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389": "test_accnt1"
      },
      "Grants": {
        "http://acs.amazonaws.com/groups/global/AllUsers": [
          "READ"
        ]
      },
      "InventoryConfigurations": [],
      "LifecycleRules": [],
      "Logging": {},
      "MetricsConfigurations": [],
      "Notifications": {},
      "Owner": {
        "ID": "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389"
      },
      "Policy": null,
      "Region": "us-east-1",
      "Replication": {},
      "Tags": {
        "LOL": "UNITTESTS"
      },
      "Versioning": {},
      "Website": null,
      "_version": 5
    }
    """)

# ACL with AuthenticatedUsers:
CONFIG_SIX = json.loads(b"""{
      "Acceleration": null,
      "AnalyticsConfigurations": [],
      "Arn": "arn:aws:s3:::bucket6",
      "Cors": [],
      "GrantReferences": {
        "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389": "test_accnt1"
      },
      "Grants": {
        "http://acs.amazonaws.com/groups/global/AuthenticatedUsers": [
          "READ"
        ]
      },
      "InventoryConfigurations": [],
      "LifecycleRules": [],
      "Logging": {},
      "MetricsConfigurations": [],
      "Notifications": {},
      "Owner": {
        "ID": "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389"
      },
      "Policy": null,
      "Region": "us-east-1",
      "Replication": {},
      "Tags": {
        "LOL": "UNITTESTS"
      },
      "Versioning": {},
      "Website": null,
      "_version": 5
    }
    """)

# ACL with LogDelivery:
CONFIG_SEVEN = json.loads(b"""{
      "Acceleration": null,
      "AnalyticsConfigurations": [],
      "Arn": "arn:aws:s3:::bucket7",
      "Cors": [],
      "GrantReferences": {
        "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389": "test_accnt1"
      },
      "Grants": {
        "http://acs.amazonaws.com/groups/s3/LogDelivery": [
          "READ"
        ]
      },
      "InventoryConfigurations": [],
      "LifecycleRules": [],
      "Logging": {},
      "MetricsConfigurations": [],
      "Notifications": {},
      "Owner": {
        "ID": "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389"
      },
      "Policy": null,
      "Region": "us-east-1",
      "Replication": {},
      "Tags": {
        "LOL": "UNITTESTS"
      },
      "Versioning": {},
      "Website": null,
      "_version": 5
    }
    """)

# ACL with deprecated friendly account name:
CONFIG_EIGHT = json.loads(b"""{
      "Acceleration": null,
      "AnalyticsConfigurations": [],
      "Arn": "arn:aws:s3:::bucket8",
      "Cors": [],
      "GrantReferences": {
        "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389": "test_accnt1"
      },
      "Grants": {
        "test_accnt2": [
          "READ"
        ]
      },
      "InventoryConfigurations": [],
      "LifecycleRules": [],
      "Logging": {},
      "MetricsConfigurations": [],
      "Notifications": {},
      "Owner": {
        "ID": "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389"
      },
      "Policy": null,
      "Region": "us-east-1",
      "Replication": {},
      "Tags": {
        "LOL": "UNITTESTS"
      },
      "Versioning": {},
      "Website": null,
      "_version": 5
    }
    """)

# ACL with deprecated thirdparty account name:
CONFIG_NINE = json.loads(b"""{
      "Acceleration": null,
      "AnalyticsConfigurations": [],
      "Arn": "arn:aws:s3:::bucket9",
      "Cors": [],
      "GrantReferences": {
        "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389": "test_accnt1"
      },
      "Grants": {
        "test_accnt3": [
          "READ"
        ]
      },
      "InventoryConfigurations": [],
      "LifecycleRules": [],
      "Logging": {},
      "MetricsConfigurations": [],
      "Notifications": {},
      "Owner": {
        "ID": "23984723987489237489237489237489uwedfjhdsjklfhksdfh2389"
      },
      "Policy": null,
      "Region": "us-east-1",
      "Replication": {},
      "Tags": {
        "LOL": "UNITTESTS"
      },
      "Versioning": {},
      "Website": null,
      "_version": 5
    }
    """)

class S3AuditorTestCase(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        S3Auditor(accounts=['TEST_ACCOUNT']).OBJECT_STORE.clear()
        self.s3_items = [
            # Same Account
            CloudAuxChangeItem(region="us-east-1", account="TEST_ACCOUNT", name="bucket1", config=CONFIG_ONE),
            # ACL with unknown cross account access
            CloudAuxChangeItem(region="us-east-1", account="TEST_ACCOUNT", name="bucket2", config=CONFIG_TWO),
            # ACL with friendly access
            CloudAuxChangeItem(region="us-east-1", account="TEST_ACCOUNT2", name="bucket3", config=CONFIG_THREE),
            # ACL with friendly thirdparty access
            CloudAuxChangeItem(region="us-east-1", account="TEST_ACCOUNT3", name="bucket4", config=CONFIG_FOUR),
            # Bucket without a policy
            CloudAuxChangeItem(region="us-east-1", account="TEST_ACCOUNT", name="bucket5", config=CONFIG_FOUR),
            # Bucket with AllUsers
            CloudAuxChangeItem(region="us-east-1", account="TEST_ACCOUNT", name="bucket5", config=CONFIG_FIVE),
            # Bucket with AuthenticatedUsers
            CloudAuxChangeItem(region="us-east-1", account="TEST_ACCOUNT", name="bucket6", config=CONFIG_SIX),
            # Bucket with LogDelivery
            CloudAuxChangeItem(region="us-east-1", account="TEST_ACCOUNT", name="bucket7", config=CONFIG_SEVEN),
            # Bucket with deprecated friendly short s3 name
            CloudAuxChangeItem(region="us-east-1", account="TEST_ACCOUNT", name="bucket8", config=CONFIG_EIGHT),
            # Bucket with deprecated thirdparty short s3 name
            CloudAuxChangeItem(region="us-east-1", account="TEST_ACCOUNT", name="bucket9", config=CONFIG_NINE)
        ]

        account_type_result = AccountType(name='AWS')
        db.session.add(account_type_result)
        db.session.commit()

        # SAME Account
        account = Account(
            identifier="012345678910", name="TEST_ACCOUNT",
            account_type_id=account_type_result.id, notes="TEST_ACCOUNT",
            third_party=False, active=True)
        account.custom_fields.append(
            AccountTypeCustomValues(
                name="canonical_id",
                value="23984723987489237489237489237489uwedfjhdsjklfhksdfh2389"))
        account.custom_fields.append(
            AccountTypeCustomValues(name="s3_name", value="test_accnt1"))

        # Friendly Account
        account2 = Account(
            identifier="012345678911", name="TEST_ACCOUNT2",
            account_type_id=account_type_result.id, notes="TEST_ACCOUNT2",
            third_party=False, active=True)
        account2.custom_fields.append(
            AccountTypeCustomValues(
                name="canonical_id",
                value="lksdjfilou32890u47238974189237euhuu128937192837189uyh1hr3"))
        account2.custom_fields.append(
            AccountTypeCustomValues(name="s3_name", value="test_accnt2"))

        # Thirdparty Account
        account3 = Account(
            identifier="012345678912", name="TEST_ACCOUNT3",
            account_type_id=account_type_result.id, notes="TEST_ACCOUNT3",
            third_party=True, active=True)
        account3.custom_fields.append(
            AccountTypeCustomValues(name="canonical_id",
            value="dsfhgiouhy23984723789y4riuwhfkajshf91283742389u823723"))
        account3.custom_fields.append(
            AccountTypeCustomValues(name="s3_name", value="test_accnt3"))

        db.session.add(account)
        db.session.add(account2)
        db.session.add(account3)
        db.session.commit()

    def run_acl_checks(self, auditor, item):
        auditor.check_acl_internet_accessible(item)
        auditor.check_acl_log_delivery(item)
        auditor.check_acl_friendly_legacy(item)
        auditor.check_acl_thirdparty_legacy(item)
        auditor.check_acl_friendly_canonical(item)
        auditor.check_acl_thirdparty_canonical(item)
        auditor.check_acl_unknown(item)

    def test_s3_acls(self):
        s3_auditor = S3Auditor(accounts=["012345678910"])
        s3_auditor.prep_for_audit()

        # CONFIG ONE:
        self.run_acl_checks(s3_auditor, self.s3_items[0])
        assert len(self.s3_items[0].audit_issues) == 0

        # CONFIG TWO:
        item = self.s3_items[1]
        self.run_acl_checks(s3_auditor, item)
        assert len(item.audit_issues) == 1
        assert item.audit_issues[0].score == 10
        assert item.audit_issues[0].issue == "Unknown Access"
        assert item.audit_issues[0].notes == "Entity: [ACL:34589673489752397023749287uiouwshjksdhfdjkshfdjkshf2381] Actions: [\"FULL_CONTROL\"]"

        # CONFIG THREE:
        item = self.s3_items[2]
        self.run_acl_checks(s3_auditor, item)
        assert len(item.audit_issues) == 1
        assert item.audit_issues[0].score == 0
        assert item.audit_issues[0].issue == "Friendly Cross Account"
        assert item.audit_issues[0].notes == "Account: [012345678911/TEST_ACCOUNT2] Entity: [ACL:lksdjfilou32890u47238974189237euhuu128937192837189uyh1hr3] Actions: [\"FULL_CONTROL\"]"

        # CONFIG FOUR:
        item = self.s3_items[3]
        self.run_acl_checks(s3_auditor, item)
        assert len(item.audit_issues) == 1
        assert item.audit_issues[0].score == 0
        assert item.audit_issues[0].issue == "Thirdparty Cross Account"
        assert item.audit_issues[0].notes == "Account: [012345678912/TEST_ACCOUNT3] Entity: [ACL:dsfhgiouhy23984723789y4riuwhfkajshf91283742389u823723] Actions: [\"FULL_CONTROL\"]"

        # CONFIG FIVE:
        item = self.s3_items[5]
        self.run_acl_checks(s3_auditor, item)
        assert len(item.audit_issues) == 1
        assert item.audit_issues[0].score == 10
        assert item.audit_issues[0].issue == "Internet Accessible"
        assert item.audit_issues[0].notes == "Account: [AWS/AWS] Entity: [ACL:http://acs.amazonaws.com/groups/global/AllUsers] Actions: [\"READ\"]"

        # CONFIG SIX:
        item = self.s3_items[6]
        self.run_acl_checks(s3_auditor, item)
        assert len(item.audit_issues) == 1
        assert item.audit_issues[0].score == 10
        assert item.audit_issues[0].issue == "Internet Accessible"
        assert item.audit_issues[0].notes == "Account: [AWS/AWS] Entity: [ACL:http://acs.amazonaws.com/groups/global/AuthenticatedUsers] Actions: [\"READ\"]"

        # CONFIG SEVEN:
        item = self.s3_items[7]
        self.run_acl_checks(s3_auditor, item)
        assert len(item.audit_issues) == 1
        assert item.audit_issues[0].score == 0
        assert item.audit_issues[0].issue == "Thirdparty Cross Account"
        assert item.audit_issues[0].notes == "Account: [AWS/AWS] Entity: [ACL:http://acs.amazonaws.com/groups/s3/LogDelivery] Actions: [\"READ\"]"

        # CONFIG EIGHT:
        item = self.s3_items[8]
        self.run_acl_checks(s3_auditor, item)
        assert len(item.audit_issues) == 1
        assert item.audit_issues[0].score == 0
        assert item.audit_issues[0].issue == "Friendly Cross Account"
        assert item.audit_issues[0].notes == "Account: [012345678911/TEST_ACCOUNT2] Entity: [ACL:test_accnt2] Actions: [\"READ\"]"

        # CONFIG NINE:
        item = self.s3_items[9]
        self.run_acl_checks(s3_auditor, item)
        assert len(item.audit_issues) == 1
        assert item.audit_issues[0].score == 0
        assert item.audit_issues[0].issue == "Thirdparty Cross Account"
        assert item.audit_issues[0].notes == "Account: [012345678912/TEST_ACCOUNT3] Entity: [ACL:test_accnt3] Actions: [\"READ\"]"

    def test_check_policy_exists(self):
        auditor = S3Auditor(accounts=['012345678910'])
        auditor.check_policy_exists(self.s3_items[4])
        assert len(self.s3_items[4].audit_issues) == 1
        assert self.s3_items[4].audit_issues[0].score == 0
        assert self.s3_items[4].audit_issues[0].issue == "POLICY - No Policy."