#     Copyright (c) 2018 AT&T Intellectual Property. All rights reserved.
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
.. module: security_monkey.tests.test_security_group
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Michael Stair <mstair@att.com>

"""
from security_monkey import AWS_DEFAULT_REGION
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.auditors.security_group import SecurityGroupAuditor
from security_monkey.watchers.security_group import SecurityGroupItem
from security_monkey.datastore import Account, AccountType
from security_monkey import db

INTERNET_SG_EGRESS = {
    'id': 'sg-12345678',
    'name': 'INTERNETSG',
    'rules': [
        {
            'cidr_ip': '0.0.0.0/0',
            'rule_type': 'egress',
            'from_port': 80,
            'to_port': 80,
            'ip_protocol': 'TCP'
        }
    ]
}

INTERNET_SG_INGRESS = {
    'id': 'sg-12345679',
    'name': 'INTERNETSG',
    'rules': [
        {
            'cidr_ip': '0.0.0.0/0',
            'rule_type': 'ingress',
            'from_port': 80,
            'to_port': 80,
            'ip_protocol': 'TCP'
        }
    ]
}

INTERNAL_SG = {
    'id': 'sg-87654321',
    'name': 'INTERNALSG',
    'rules': [
        {
            'cidr_ip': '10.0.0.0/8',
            'rule_type': 'ingress',
            'from_port': 80,
            'to_port': 80,
            'ip_protocol': 'TCP'
        }
    ]
}

class SecurityGroupAuditorTestCase(SecurityMonkeyTestCase):

    def pre_test_setup(self):

        SecurityGroupAuditor(accounts=['TEST_ACCOUNT']).OBJECT_STORE.clear()
        account_type_result = AccountType(name='AWS')
        db.session.add(account_type_result)
        db.session.commit()

        # main
        account = Account(identifier="123456789123", name="TEST_ACCOUNT",
                          account_type_id=account_type_result.id, notes="TEST_ACCOUNT",
                          third_party=False, active=True)

        db.session.add(account)
        db.session.commit()

    def test_check_securitygroup_ec2_rfc1918(self):
        auditor = SecurityGroupAuditor(accounts=['TEST_ACCOUNT'])
        auditor.prep_for_audit()

        item = SecurityGroupItem(region=AWS_DEFAULT_REGION, account='TEST_ACCOUNT', name='INTERNAL_SG', 
                                    config=INTERNAL_SG)

        auditor.check_securitygroup_ec2_rfc1918(item)
        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].score, 0)

    def test_check_internet_accessible_ingress(self):
        auditor = SecurityGroupAuditor(accounts=['TEST_ACCOUNT'])
        auditor.prep_for_audit()

        item = SecurityGroupItem(region=AWS_DEFAULT_REGION, account='TEST_ACCOUNT', name='INTERNET_SG_INGRESS', 
                                    config=INTERNET_SG_INGRESS)

        auditor.check_internet_accessible_ingress(item)
        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].score, 0)

    def test_check_internet_accessible_egress(self):
        auditor = SecurityGroupAuditor(accounts=['TEST_ACCOUNT'])
        auditor.prep_for_audit()

        item = SecurityGroupItem(region=AWS_DEFAULT_REGION, account='TEST_ACCOUNT', name='INTERNET_SG_EGRESS', 
                                    config=INTERNET_SG_EGRESS)

        auditor.check_internet_accessible_egress(item)
        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].score, 0)