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


class S3AuditorTestCase(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        self.s3_items = [
            CloudAuxChangeItem(region="us-east-1", account="TEST_ACCOUNT", name="bucket1", config=CONFIG_ONE),
            CloudAuxChangeItem(region="us-east-1", account="TEST_ACCOUNT", name="bucket2", config=CONFIG_TWO),
            CloudAuxChangeItem(region="us-east-1", account="TEST_ACCOUNT2", name="bucket3", config=CONFIG_THREE),
            CloudAuxChangeItem(region="us-east-1", account="TEST_ACCOUNT3", name="bucket4", config=CONFIG_FOUR)
        ]

        account_type_result = AccountType(name='AWS')
        db.session.add(account_type_result)
        db.session.commit()

        account = Account(identifier="012345678910", name="TEST_ACCOUNT",
                          account_type_id=account_type_result.id, notes="TEST_ACCOUNT",
                          third_party=False, active=True)
        account.custom_fields.append(AccountTypeCustomValues(name="canonical_id",
                                                             value="23984723987489237489237489237489uwedfjhdsjklfhksdf"
                                                                   "h2389"))
        account.custom_fields.append(AccountTypeCustomValues(name="s3_name", value="test_accnt1"))

        account2 = Account(identifier="012345678911", name="TEST_ACCOUNT2",
                           account_type_id=account_type_result.id, notes="TEST_ACCOUNT2",
                           third_party=False, active=True)

        account2.custom_fields.append(AccountTypeCustomValues(name="canonical_id",
                                                              value="lksdjfilou32890u47238974189237euhuu128937192837189"
                                                                    "uyh1hr3"))
        account2.custom_fields.append(AccountTypeCustomValues(name="s3_name", value="test_accnt2"))

        account3 = Account(identifier="012345678912", name="TEST_ACCOUNT3",
                           account_type_id=account_type_result.id, notes="TEST_ACCOUNT3",
                           third_party=True, active=True)

        account3.custom_fields.append(AccountTypeCustomValues(name="canonical_id",
                                                              value="dsfhgiouhy23984723789y4riuwhfkajshf91283742389u"
                                                                    "823723"))
        account3.custom_fields.append(AccountTypeCustomValues(name="s3_name", value="test_accnt3"))

        db.session.add(account)
        db.session.add(account2)
        db.session.add(account3)
        db.session.commit()

    def test_s3_acls(self):
        s3_auditor = S3Auditor(accounts=["012345678910"])

        # CONFIG ONE:
        s3_auditor.check_acl(self.s3_items[0])
        assert len(self.s3_items[0].audit_issues) == 0

        # CONFIG TWO:
        s3_auditor.check_acl(self.s3_items[1])
        assert len(self.s3_items[1].audit_issues) == 1
        assert self.s3_items[1].audit_issues[0].score == 10
        assert self.s3_items[1].audit_issues[0].issue == "ACL - Unknown Cross Account Access."

        # CONFIG THREE:
        s3_auditor.check_acl(self.s3_items[2])
        assert len(self.s3_items[2].audit_issues) == 1
        assert self.s3_items[2].audit_issues[0].score == 0
        assert self.s3_items[2].audit_issues[0].issue == "ACL - Friendly Account Access."

        # CONFIG FOUR:
        s3_auditor.check_acl(self.s3_items[3])
        assert len(self.s3_items[3].audit_issues) == 1
        assert self.s3_items[3].audit_issues[0].score == 0
        assert self.s3_items[3].audit_issues[0].issue == "ACL - Friendly Third Party Access."
