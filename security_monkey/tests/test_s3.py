#     Copyright 2014 Netflix, Inc.
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
from security_monkey.watchers.s3 import S3Item
from security_monkey.auditors.s3 import S3Auditor
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.constants import S3_ACCOUNT_NAMES
from mock import patch
from mock import MagicMock


class S3TestCase(SecurityMonkeyTestCase):
   
    @patch('security_monkey.common.sts_connect.connect') 
    def test_0_s3_slurp(self, test_patch):
        """Slurp should add an exception to the exceptions map when
           slurping accounts that don't exist."""
        from security_monkey.watchers.s3 import S3
        import boto.s3
        
        test_patch.return_value = None
        accounts = ['doesntexit1', 'doesntexist2']
        cw = S3(accounts=accounts, debug=True)
        (items, el) = cw.slurp()
        for account in accounts:
            self.assertIn(('s3', account), el)
    
    @patch('security_monkey.common.sts_connect.connect') 
    def test_1_s3_slurp(self, test_patch):
        """Should add an exception when ???"""
        
        class Grant(object):
            display_name = 'test_acl'
            permission = 'READ'

        class ACL(object):
            
            def __init__(self):
                self.grants = [Grant(), Grant(), Grant()]
            
        class intraACL(object):
            acl = ACL()
            
            def to_xml(self):
                return ''
        
        class Bucket(object):
            name = 'test_bucket_name'                
            
            def get_location(self):
                return None
            
            def get_acl(self):
                return intraACL()
            
            def get_policy(self):
                return '{ "fake": "policy" }'
            
            def get_versioning_status(self):
                return ""
       
        class MockS3(object):
            def get_bucket(self, blah):
                return Bucket()
            
            def get_all_buckets(self):
                return [Bucket(), Bucket()]
            
            def close(self):
                pass
        
        from security_monkey.watchers.s3 import S3
        test_patch.return_value = MockS3()
        accounts = ['testaccount']
        cw = S3(accounts=accounts, debug=True)
        (items, el) = cw.slurp()
        for item in items:
            print "Item: {} - {}".format(item.name, item.new_config)
        
        self.assertEqual(len(items), 2)
        self.assertEqual(len(el), 0)
    
    def test_auditor_acl_authenticated_users(self):
        au = S3Auditor(debug=True)
        data = {
            'grants': {
                'http://acs.amazonaws.com/groups/global/AuthenticatedUsers':
                    [
                        'READ', 'WRITE'
                    ],
            },
        }
        obj = S3Item(region='test-region', account='test-account', name='test-name', config=data)
        au.check_acl(obj)
        self.assertEquals(len(obj.audit_issues), 1)
        if len(obj.audit_issues) == 1:
            for issue in obj.audit_issues:
                self.assertEquals(issue.score, 10)
                self.assertRegexpMatches(issue.issue, "ACL - AuthenticatedUsers USED. ")
                self.assertEquals(issue.notes, 'READ,WRITE')
                
    def test_auditor_acl_all_users(self):
        au = S3Auditor(debug=True)
        data = {
            'grants': {
                'http://acs.amazonaws.com/groups/global/AllUsers':
                    [
                        'READ', 'WRITE'
                    ],
            },
        }
        obj = S3Item(region='test-region', account='test-account', name='test-name', config=data)
        au.check_acl(obj)
        self.assertEquals(len(obj.audit_issues), 1)
        if len(obj.audit_issues) == 1:
            for issue in obj.audit_issues:
                self.assertEquals(issue.score, 10)
                self.assertRegexpMatches(issue.issue, "ACL - AllUsers USED.")
                self.assertEquals(issue.notes, 'READ,WRITE')
            
    def test_auditor_acl_log_delivery(self):
        au = S3Auditor(debug=True)
        data = {
            'grants': {
                'http://acs.amazonaws.com/groups/s3/LogDelivery':
                    [
                        'READ', 'WRITE'
                    ],
            },
        }
        obj = S3Item(region='test-region', account='test-account', name='test-name', config=data)
        au.check_acl(obj)
        self.assertEquals(len(obj.audit_issues), 1)
        if len(obj.audit_issues) == 1:
            for issue in obj.audit_issues:
                self.assertEquals(issue.score, 0)
                self.assertRegexpMatches(issue.issue, "ACL - LogDelivery USED.")
                self.assertEquals(issue.notes, 'READ,WRITE')

    def test_auditor_acl_friendly_account_access(self):
        # "Mocking" out S3_ACCOUNT_NAMES
        import security_monkey
        security_monkey.constants.S3_ACCOUNT_NAMES = ['TEST_FRIEND']
        
        au = S3Auditor(debug=True)
        data = {
            'grants': {
                'TEST_FRIEND':
                    [
                        'READ', 'WRITE'
                    ],
            },
        }
        obj = S3Item(region='test-region', account='test-account', name='test-name', config=data)
        au.check_acl(obj)
        self.assertEquals(len(obj.audit_issues), 1)
        if len(obj.audit_issues) == 1:
            for issue in obj.audit_issues:
                self.assertEquals(issue.score, 0)
                self.assertRegexpMatches(issue.issue, "ACL - Friendly Account Access")
                self.assertEquals(issue.notes, 'READ,WRITE TEST_FRIEND')
                
    def test_auditor_acl_third_party_access(self):
        # "Mocking" out S3_THIRD_PARTY_ACCOUNTS
        import security_monkey
        security_monkey.constants.S3_THIRD_PARTY_ACCOUNTS = ['TEST_THIRD_PARTY_FRIEND']
        
        au = S3Auditor(debug=True)
        data = {
            'grants': {
                'TEST_THIRD_PARTY_FRIEND':
                    [
                        'READ', 'WRITE'
                    ],
            },
        }
        obj = S3Item(region='test-region', account='test-account', name='test-name', config=data)
        au.check_acl(obj)
        self.assertEquals(len(obj.audit_issues), 1)
        if len(obj.audit_issues) == 1:
            for issue in obj.audit_issues:
                self.assertEquals(issue.score, 0)
                self.assertRegexpMatches(issue.issue, "ACL - Friendly Third Party Access.")
                self.assertEquals(issue.notes, 'READ,WRITE TEST_THIRD_PARTY_FRIEND')
                
                
    def test_auditor_acl_unkown_cross_account_access(self):
        au = S3Auditor(debug=True)
        data = {
            'grants': {
                'UNKOWN_ACCOUNT_DOESNT_EXIST':
                    [
                        'READ', 'WRITE'
                    ],
            },
        }
        obj = S3Item(region='test-region', account='test-account', name='test-name', config=data)
        au.check_acl(obj)
        self.assertEquals(len(obj.audit_issues), 1)
        if len(obj.audit_issues) == 1:
            for issue in obj.audit_issues:
                self.assertEquals(issue.score, 10)
                self.assertRegexpMatches(issue.issue, "ACL - Unknown Cross Account Access.")
                self.assertEquals(issue.notes, 'READ,WRITE UNKOWN_ACCOUNT_DOESNT_EXIST')
    
    def test_auditor_policy_allow_all(self):
        au = S3Auditor(debug = True)
        data = {
            'policy': {
                'Statement': [
                    {
                        'Effect': 'Allow',
                        'Principal': '*'
                    }
                ]
            }
        }
        obj = S3Item(region='test-region', account='test-account', name='test-name', config=data)
        au.check_policy(obj)
        self.assertEquals(len(obj.audit_issues), 1)
        if len(obj.audit_issues) == 1:
            for issue in obj.audit_issues:
                self.assertEquals(issue.score, 10)
                self.assertRegexpMatches(issue.issue, "POLICY - This Policy Allows Access From Anyone.")

    def test_auditor_policy_9_cross_account_friendly(self):
        friend_name = 'friendly'
        from security_monkey.constants import Constants
        Constants.account_by_number = MagicMock(return_value=friend_name)
        
        au = S3Auditor(debug = True)
        data = {
            'policy': {
                'Statement': [
                    {
                        'Effect': 'Allow',
                        'Principal': {
                            'AWS': 'arn:aws:iam::0123456789:role/Test'
                        }
                    }
                ]
            }
        }
        obj = S3Item(region='test-region', account='test-account', name='test-name', config=data)
        au.check_policy(obj)
        self.assertEquals(len(obj.audit_issues), 1)
        if len(obj.audit_issues) == 1:
            for issue in obj.audit_issues:
                self.assertEquals(issue.score, 0)
                self.assertRegexpMatches(issue.issue, "POLICY - Friendly Account Access.")
                self.assertRegexpMatches(issue.notes, friend_name)

    def test_auditor_policy_8_cross_account_third_party(self):
        import security_monkey
        security_monkey.constants.KNOWN_FRIENDLY_THIRDPARTY_ACCOUNTS = {
            '0123456789': 'friendly'
        }
        
        au = S3Auditor(debug = True)
        data = {
            'policy': {
                'Statement': [
                    {
                        'Effect': 'Allow',
                        'Principal': {
                            'AWS': 'arn:aws:iam::0123456789:role/Test'
                        }
                    }
                ]
            }
        }
        obj = S3Item(region='test-region', account='test-account', name='test-name', config=data)
        au.check_policy(obj)
        self.assertEquals(len(obj.audit_issues), 1)
        if len(obj.audit_issues) == 1:
            for issue in obj.audit_issues:
                self.assertEquals(issue.score, 0)
                self.assertRegexpMatches(issue.issue, "POLICY - Friendly Third Party Account Access.")
                self.assertEquals(issue.notes, 'friendly')

    def test_auditor_policy_7_cross_account_unknown(self):
                
        au = S3Auditor(debug = True)
        data = {
            'policy': {
                'Statement': [
                    {
                        'Effect': 'Allow',
                        'Principal': {
                            'AWS': 'arn:aws:iam::11111111111:role/Test'
                        }
                    }
                ]
            }
        }
        obj = S3Item(region='test-region', account='test-account', name='test-name', config=data)
        au.check_policy(obj)
        self.assertEquals(len(obj.audit_issues), 1)
        if len(obj.audit_issues) == 1:
            for issue in obj.audit_issues:
                self.assertEquals(issue.score, 10)
                self.assertRegexpMatches(issue.issue, "POLICY - Unknown Cross Account Access")
                self.assertRegexpMatches(issue.notes, 'Account ID: 11111111111 ARN: arn:aws:iam::11111111111:role/Test')

    def test_auditor_policy_6_conditionals(self):
                
        au = S3Auditor(debug = True)
        data = {
            'policy': {
                'Statement': [
                    {
                        'Effect': 'Allow',
                        'Principal': {
                            'AWS': 'arn:aws:iam::33333333333:role/Test'
                        }, 
                        'Condition': 'Blah'
                    }
                ]
            }
        }
        obj = S3Item(region='test-region', account='test-account', name='test-name', config=data)
        au.check_policy(obj)
        # Any policy that has conditions must also have
        # either friendly, third party, or unknown access.
        # So the length will always be 2 here:
        self.assertEquals(len(obj.audit_issues), 2)
        if len(obj.audit_issues) == 1:
            for issue in obj.audit_issues:
                if issue.issue == 'POLICY - This policy has conditions.':
                    self.assertEquals(issue.score, 3)
                    self.assertRegexpMatches(issue.issue, "POLICY - This policy has conditions.")
