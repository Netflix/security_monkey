from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.auditor import Entity
from security_monkey.auditors.resource_policy_auditor import ResourcePolicyAuditor
from security_monkey import db
from security_monkey.watcher import ChangeItem
from security_monkey.datastore import Datastore
from security_monkey.datastore import Account, AccountType, ItemAudit
from collections import namedtuple
from policyuniverse.policy import Policy
from copy import deepcopy


Item = namedtuple('Item', 'config account')

# Example KMS Config
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
  "Policy": [
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
  "Arn": "arn:aws:kms:us-east-1:123456789123:key/key_id",
  "AWSAccountId": "123456789123"
}


class ResourcePolicyTestCase(SecurityMonkeyTestCase):
    
    def pre_test_setup(self):
        ResourcePolicyAuditor(accounts=['TEST_ACCOUNT']).OBJECT_STORE.clear()
        account_type_result = AccountType(name='AWS')
        db.session.add(account_type_result)
        db.session.commit()

        # main
        account = Account(identifier="012345678910", name="TEST_ACCOUNT",
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
        
        datastore = Datastore()
        # S3
        datastore.store('s3', 'us-east-1', 'TEST_ACCOUNT', 'my-test-s3-bucket',
            True, dict(), arn='arn:aws:s3:::my-test-s3-bucket')

        datastore.store('s3', 'us-east-1', 'TEST_ACCOUNT_TWO', 'my-test-s3-bucket-two',
            True, dict(), arn='arn:aws:s3:::my-test-s3-bucket-two')

        datastore.store('s3', 'us-east-1', 'TEST_ACCOUNT_THREE', 'my-test-s3-bucket-three',
            True, dict(), arn='arn:aws:s3:::my-test-s3-bucket-three')

        # IAM User
        datastore.store('iamuser', 'us-east-1', 'TEST_ACCOUNT', 'my-test-iam-user',
            True, dict(UserId='AIDA11111111111111111', UserName='my-test-iam-user'),
            arn='arn:aws:iam::012345678910:user/my-test-iam-user')

        datastore.store('iamuser', 'us-east-1', 'TEST_ACCOUNT_TWO', 'my-test-iam-user-two',
            True, dict(UserId='AIDA22222222222222222', UserName='my-test-iam-user-two'),
            arn='arn:aws:iam::222222222222:user/my-test-iam-user-two')

        datastore.store('iamuser', 'us-east-1', 'TEST_ACCOUNT_THREE', 'my-test-iam-user-three',
            True, dict(UserId='AIDA33333333333333333', UserName='my-test-iam-user-three'),
            arn='arn:aws:iam::333333333333:user/my-test-iam-user-three')

        # IAM Role
        datastore.store('iamrole', 'us-east-1', 'TEST_ACCOUNT', 'my-test-iam-role',
            True, dict(RoleId='AISA11111111111111111', RoleName='my-test-iam-role'),
            arn='arn:aws:iam::012345678910:role/my-test-iam-role')

        datastore.store('iamrole', 'us-east-1', 'TEST_ACCOUNT_TWO', 'my-test-iam-role-two',
            True, dict(RoleId='AISA22222222222222222', RoleName='my-test-iam-role-two'),
            arn='arn:aws:iam::222222222222:role/my-test-iam-role-two')

        datastore.store('iamrole', 'us-east-1', 'TEST_ACCOUNT_THREE', 'my-test-iam-role-three',
            True, dict(RoleId='AISA33333333333333333', RoleName='my-test-iam-role-three'),
            arn='arn:aws:iam::333333333333:role/my-test-iam-role-three')

        # NAT Gateway
        datastore.store('natgateway', 'us-east-1', 'TEST_ACCOUNT', 'my-test-natgateway',
            True, dict(nat_gateway_addresses=[dict(public_ip='54.11.11.11', private_ip='172.16.11.11')]),
            arn=None)  # natgateway has no ARN :(

        datastore.store('natgateway', 'us-east-1', 'TEST_ACCOUNT_TWO', 'my-test-natgateway-two',
            True, dict(nat_gateway_addresses=[dict(public_ip='54.22.22.22', private_ip='172.16.22.22')]),
            arn=None)  # natgateway has no ARN :(

        datastore.store('natgateway', 'us-east-1', 'TEST_ACCOUNT_THREE', 'my-test-natgateway-three',
            True, dict(nat_gateway_addresses=[dict(public_ip='54.33.33.33', private_ip='172.16.33.33')]),
            arn=None)  # natgateway has no ARN :(

        # VPC
        datastore.store('vpc', 'us-east-1', 'TEST_ACCOUNT', 'my-test-vpc', True,
            dict(id='vpc-11111111', cidr_block='10.1.1.1/18'),
            arn='arn:aws:ec2:us-east-1:012345678910:vpc/vpc-11111111')

        datastore.store('vpc', 'us-east-1', 'TEST_ACCOUNT_TWO', 'my-test-vpc-two', True,
            dict(id='vpc-22222222', cidr_block='10.2.2.2/18'),
            arn='arn:aws:ec2:us-east-1:222222222222:vpc/vpc-22222222')

        datastore.store('vpc', 'us-east-1', 'TEST_ACCOUNT_THREE', 'my-test-vpc-three', True,
            dict(id='vpc-33333333', cidr_block='10.3.3.3/18'),
            arn='arn:aws:ec2:us-east-1:333333333333:vpc/vpc-33333333')

        # VPC Service Endpoint (For S3 and things)
        datastore.store('endpoint', 'us-east-1', 'TEST_ACCOUNT', 'my-test-vpce',
            True, dict(id='vpce-11111111'),
            arn=None)  # vpce has no ARN :(

        datastore.store('endpoint', 'us-east-1', 'TEST_ACCOUNT_TWO', 'my-test-vpce-two',
            True, dict(id='vpce-22222222'),
            arn=None)  # vpce has no ARN :(

        datastore.store('endpoint', 'us-east-1', 'TEST_ACCOUNT_THREE', 'my-test-vpce-three',
            True, dict(id='vpce-33333333'),
            arn=None)  # vpce has no ARN :(

    def test_load_policies(self):
        
        policy01 = dict(Version='2012-10-08', Statement=[])
        test_item = Item(account=None, config=dict(Policy=policy01))
        
        rpa = ResourcePolicyAuditor(accounts=["012345678910"])
        # Policy class has no equivelance test at the moment.
        # Compare the underlying dicts instead
        policies = [policy.policy for policy in rpa.load_resource_policies(test_item)]
        self.assertEqual([policy01], policies)
        
        
        policy02 = dict(Version='2012-10-08', Statement=[
            dict(
                Effect='Allow',
                Action='*',
                Resource='*')])

        policy03 = dict(Version='2012-10-08', Statement=[
            dict(
                Effect='Allow',
                Action='lambda:*',
                Resource='*')])

        policy04 = dict(Version='2012-10-08', Statement=[
            dict(
                Effect='Allow',
                Action='ec2:*',
                Resource='*')])

        # simulate a lambda function, which contains multiple policies
        test_item = Item(
            account=None,
            config=dict(
                Policies=dict(
                    Aliases=dict(
                        stable=policy01),
                    DEFAULT=policy02,
                    Versions={
                        "3": policy03,
                        "4": policy04
                    })))
            
        rpa.policy_keys = ['Policies$Aliases$*', 'Policies$DEFAULT', 'Policies$Versions$*']
        policies = [policy.policy for policy in rpa.load_resource_policies(test_item)]
        self.assertEqual([policy01, policy02, policy03, policy04], policies)
        
    def test_prep_for_audit(self):
        rpa = ResourcePolicyAuditor(accounts=["012345678910"])
        rpa.prep_for_audit()

        self.assertEqual(rpa.OBJECT_STORE['s3']['my-test-s3-bucket'], set(['012345678910']))
        self.assertEqual(rpa.OBJECT_STORE['ACCOUNTS']['FRIENDLY'], set(['012345678910', '222222222222']))
        self.assertEqual(rpa.OBJECT_STORE['ACCOUNTS']['THIRDPARTY'], set(['333333333333']))

        self.assertEqual(
            set(rpa.OBJECT_STORE['userid'].keys()),
            set(['AIDA11111111111111111', 'AISA11111111111111111',
                 'AIDA22222222222222222', 'AISA22222222222222222',
                 'AIDA33333333333333333', 'AISA33333333333333333']))

        from ipaddr import IPNetwork
        self.assertEqual(
            set(rpa.OBJECT_STORE['cidr'].keys()), 
            set(['10.1.1.1/18', '172.16.11.11/32', '54.11.11.11/32',
                 '10.2.2.2/18', '172.16.22.22/32', '54.22.22.22/32',
                 '10.3.3.3/18', '172.16.33.33/32', '54.33.33.33/32']))

        self.assertEqual(
            set(rpa.OBJECT_STORE['vpc'].keys()),
            set(['vpc-11111111', 'vpc-22222222', 'vpc-33333333']))

        self.assertEqual(
            set(rpa.OBJECT_STORE['vpce'].keys()),
            set(['vpce-11111111', 'vpce-22222222', 'vpce-33333333']))
    
    def test_inspect_entity(self):
        rpa = ResourcePolicyAuditor(accounts=["012345678910"])
        rpa.prep_for_audit()

        # All conditions are SAME account.
        policy01 = dict(
            Version='2010-08-14',
            Statement=[
                dict(
                    Effect='Allow',
                    Principal='arn:aws:iam::012345678910:root',
                    Action=['ec2:*'],
                    Resource='*',
                    Condition={
                        'StringEquals': {
                            'AWS:SourceOwner': '012345678910',
                            'AWS:SourceARN': 'arn:aws:iam::012345678910:root',
                            'AWS:SourceVPC': 'vpc-11111111',
                            'AWS:Sourcevpce': 'vpce-11111111',
                            'AWS:username': 'my-test-iam-role'
                        }, 'StringLike': {
                            'AWS:userid': ['AIDA11111111111111111:*', 'AISA11111111111111111:*']
                        }, 'IpAddress': {
                            'AWS:SourceIP': ['54.11.11.11', '10.1.1.1/18', '172.16.11.11']
                        }})])

        test_item = Item(account='TEST_ACCOUNT', config=None)
        policy = Policy(policy01)
        for who in policy.whos_allowed():
            entity = Entity.from_tuple(who)
            self.assertEqual(set(['SAME']), rpa.inspect_entity(entity, test_item))

        # All conditions are FRIENDLY account.
        policy02 = dict(
            Version='2010-08-14',
            Statement=[
                dict(
                    Effect='Allow',
                    Principal='arn:aws:iam::222222222222:root',
                    Action=['ec2:*'],
                    Resource='*',
                    Condition={
                        'StringEquals': {
                            'AWS:SourceOwner': '222222222222',
                            'AWS:SourceARN': 'arn:aws:s3:::my-test-s3-bucket-two',
                            'AWS:SourceVPC': 'vpc-22222222',
                            'AWS:Sourcevpce': 'vpce-22222222',
                            'AWS:username': 'my-test-iam-role-two'
                        }, 'StringLike': {
                            'AWS:userid': ['AIDA22222222222222222:*', 'AISA22222222222222222:*']
                        }, 'IpAddress': {
                            'AWS:SourceIP': ['54.22.22.22', '10.2.2.2/18', '172.16.22.22']
                        }})])

        test_item = Item(account='TEST_ACCOUNT', config=None)
        policy = Policy(policy02)
        for who in policy.whos_allowed():
            entity = Entity.from_tuple(who)
            self.assertEqual(set(['FRIENDLY']), rpa.inspect_entity(entity, test_item))

        # All conditions are THIRDPARTY account.
        policy03 = dict(
            Version='2010-08-14',
            Statement=[
                dict(
                    Effect='Allow',
                    Principal='arn:aws:iam::333333333333:root',
                    Action=['ec2:*'],
                    Resource='*',
                    Condition={
                        'StringEquals': {
                            'AWS:SourceOwner': '333333333333',
                            'AWS:SourceARN': 'arn:aws:iam::333333333333:root',
                            'AWS:SourceVPC': 'vpc-33333333',
                            'AWS:Sourcevpce': 'vpce-33333333',
                            'AWS:username': 'my-test-iam-role-three'
                        }, 'StringLike': {
                            'AWS:userid': ['AIDA33333333333333333:*', 'AISA33333333333333333:*']
                        }, 'IpAddress': {
                            'AWS:SourceIP': ['54.33.33.33', '10.3.3.3/18', '172.16.33.33']
                        }})])

        test_item = Item(account='TEST_ACCOUNT', config=None)
        policy = Policy(policy03)
        for who in policy.whos_allowed():
            entity = Entity.from_tuple(who)
            self.assertEqual(set(['THIRDPARTY']), rpa.inspect_entity(entity, test_item))

        # All conditions are from an UNKNOWN account.
        policy04 = dict(
            Version='2010-08-14',
            Statement=[
                dict(
                    Effect='Allow',
                    Principal='arn:aws:iam::444444444444:root',
                    Action=['ec2:*'],
                    Resource='*',
                    Condition={
                        'StringEquals': {
                            'AWS:SourceOwner': '444444444444',
                            'AWS:SourceARN': 'arn:aws:iam::444444444444:root',
                            'AWS:SourceVPC': 'vpc-44444444',
                            'AWS:Sourcevpce': 'vpce-44444444',
                            'AWS:username': 'my-test-iam-role-four'
                        }, 'StringLike': {
                            'AWS:userid': ['AIDA44444444444444444:*', 'AISA44444444444444444:*']
                        }, 'IpAddress': {
                            'AWS:SourceIP': ['54.44.44.44', '10.4.4.4/18', '172.16.44.44']
                        }})])

        test_item = Item(account='TEST_ACCOUNT', config=None)
        policy = Policy(policy04)
        for who in policy.whos_allowed():
            entity = Entity.from_tuple(who)
            self.assertEqual(set(['UNKNOWN']), rpa.inspect_entity(entity, test_item))

    def test_check_internet_accessible(self):
        rpa = ResourcePolicyAuditor(accounts=["012345678910"])
        rpa.prep_for_audit()

        policy01 = dict(
            Version='2010-08-14',
            Statement=[
                dict(
                    Effect='Allow',
                    Principal='arn:aws:iam::*:root',
                    Action=['ec2:*'],
                    Resource='*')])

        test_item = Item(account='TEST_ACCOUNT', config=dict(Policy=policy01))
        def mock_add_issue(score, issue, item, notes=None, action_instructions=None):
            self.assertEqual(10, score)
            self.assertEqual('Internet Accessible', issue)
            self.assertEqual('Entity: [principal:*] Actions: ["ec2:*"]', notes)

        rpa.add_issue = lambda *args, **kwargs: mock_add_issue(*args, **kwargs)
        rpa.check_internet_accessible(test_item)

        policy02 = dict(
            Version='2010-08-14',
            Statement=[
                dict(
                    Effect='Allow',
                    Principal='arn:aws:iam::012345678910:root',
                    Action=['ec2:*'],
                    Resource='*')])

        test_item = Item(account='TEST_ACCOUNT', config=dict(Policy=policy02))
        
        def mock_add_issue_two(score, issue, item, notes=None):
            # should not get here
            self.assertTrue(False)

        rpa.add_issue = lambda *args, **kwargs: mock_add_issue_two(*args, **kwargs)
        rpa.check_internet_accessible(test_item)
    
    def test_check_friendly_cross_account(self):
        rpa = ResourcePolicyAuditor(accounts=["012345678910"])
        rpa.prep_for_audit()

        policy01 = dict(
            Version='2010-08-14',
            Statement=[
                dict(
                    Effect='Allow',
                    Principal='arn:aws:iam::222222222222:root',
                    Action=['ec2:*'],
                    Resource='*')])

        test_item = Item(account='TEST_ACCOUNT', config=dict(Policy=policy01))
        def mock_add_issue(score, issue, item, notes=None):
            self.assertEqual(0, score)
            self.assertEqual('Friendly Cross Account', issue)
            self.assertEqual('Account: [222222222222/TEST_ACCOUNT_TWO] Entity: [principal:arn:aws:iam::222222222222:root] Actions: ["ec2:*"]', notes)

        rpa.add_issue = lambda *args, **kwargs: mock_add_issue(*args, **kwargs)
        rpa.check_friendly_cross_account(test_item)

    def test_check_unknown_cross_account(self):
        rpa = ResourcePolicyAuditor(accounts=["012345678910"])
        rpa.prep_for_audit()

        policy01 = dict(
            Version='2010-08-14',
            Statement=[
                dict(
                    Effect='Allow',
                    Principal='arn:aws:iam::444444444444:root',
                    Action=['ec2:*'],
                    Resource='*')])

        test_item = Item(account='TEST_ACCOUNT', config=dict(Policy=policy01))
        def mock_add_issue(score, issue, item, notes=None):
            self.assertEqual(10, score)
            self.assertEqual('Unknown Access', issue)
            self.assertEqual('Entity: [principal:arn:aws:iam::444444444444:root] Actions: ["ec2:*"]', notes)

        rpa.add_issue = lambda *args, **kwargs: mock_add_issue(*args, **kwargs)
        rpa.check_unknown_cross_account(test_item)

    def test_check_thirdparty_cross_account(self):
        rpa = ResourcePolicyAuditor(accounts=['TEST_ACCOUNT'])
        rpa.prep_for_audit()

        key0_friendly_cross_account = deepcopy(key0)
        key0_friendly_cross_account['Policy'][0]['Statement'][0]['Principal']['AWS'] \
            = 'arn:aws:iam::333333333333:role/SomeRole'
        item = ChangeItem(
            account='TEST_ACCOUNT',
            arn='arn:aws:kms:us-east-1:012345678910:key/key_id',
            new_config=key0_friendly_cross_account)
        rpa.check_thirdparty_cross_account(item)
        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].score, 0)

    def test_check_root_cross_account(self):
        rpa = ResourcePolicyAuditor(accounts=['TEST_ACCOUNT'])
        rpa.prep_for_audit()

        key0_friendly_cross_account = deepcopy(key0)
        key0_friendly_cross_account['Policy'][0]['Statement'][0]['Principal']['AWS'] \
            = 'arn:aws:iam::222222222222:root'
        item = ChangeItem(
            account='TEST_ACCOUNT',
            arn='arn:aws:kms:us-east-1:012345678910:key/key_id',
            new_config=key0_friendly_cross_account)
        rpa.check_root_cross_account(item)
        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].score, 6)
