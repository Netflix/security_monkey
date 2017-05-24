from security_monkey.datastore import Account, AccountType
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey import db


INTERNET_ELB = {
  "Arn": "arn:aws:elasticloadbalancing:us-east-1:012345678901:loadbalancer/MyELB",
  "Attributes": {
    "ConnectionDraining": {
      "Enabled": False,
      "Timeout": 300
    },
    "CrossZoneLoadBalancing": {
      "Enabled": False
    },
    "ConnectionSettings": {
      "IdleTimeout": 60
    },
    "AccessLog": {
      "S3BucketPrefix": "test",
      "Enabled": True,
      "EmitInterval": 5,
      "S3BucketName": "some-log-bucket"
    }
  },
  "AvailabilityZones": [
    "us-east-1b"
  ],
  "BackendServerDescriptions": [],
  "CanonicalHostedZoneNameID": "Z3DZXE0Q79N41H",
  "CreatedTime": "2015-07-07 19:15:06.490000+00:00",
  "DNSName": "MyELB-1885487881.us-east-1.elb.amazonaws.com",
  "HealthCheck": {
    "HealthyThreshold": 2,
    "Interval": 30,
    "Target": "HTTP:5050/health",
    "Timeout": 5,
    "UnhealthyThreshold": 2
  },
  "Instances": [],
  "ListenerDescriptions": [
    {
      "InstancePort": 80,
      "PolicyNames": [],
      "LoadBalancerPort": 80,
      "Protocol": "HTTP",
      "InstanceProtocol": "HTTP"
    },
    {
      "InstancePort": 2181,
      "PolicyNames": [],
      "LoadBalancerPort": 2181,
      "Protocol": "TCP",
      "InstanceProtocol": "TCP"
    },
    {
      "InstancePort": 5050,
      "PolicyNames": [],
      "LoadBalancerPort": 5050,
      "Protocol": "HTTP",
      "InstanceProtocol": "HTTP"
    },
    {
      "InstancePort": 8080,
      "PolicyNames": [],
      "LoadBalancerPort": 8080,
      "Protocol": "HTTP",
      "InstanceProtocol": "HTTP"
    },
    {
      "InstancePort": 8181,
      "PolicyNames": [],
      "LoadBalancerPort": 8181,
      "Protocol": "HTTP",
      "InstanceProtocol": "HTTP"
    },
    {
      "InstancePort": 80,
      "Protocol": "HTTPS",
      "InstanceProtocol": "HTTP",
      "LoadBalancerPort": 443,
      "PolicyNames": [
        "ELBSecurityPolicy-2016-08"
      ],
      "SSLCertificateId": "arn:aws:iam::012345678901:server-certificate/somecert-20170511-20180511"
    }
  ],
  "LoadBalancerName": "MyELB",
  "Policies": {
    "LBCookieStickinessPolicies": [],
    "AppCookieStickinessPolicies": [],
    "OtherPolicies": [
      "ELBSecurityPolicy-2016-08"
    ]
  },
  "PolicyDescriptions": {
    "ELBSecurityPolicy-2016-08": {
      "reference_security_policy": "ELBSecurityPolicy-2016-08",
      "supported_ciphers": [
        "AES128-GCM-SHA256",
        "AES128-SHA",
        "AES128-SHA256",
        "AES256-GCM-SHA384",
        "AES256-SHA",
        "AES256-SHA256",
        "ECDHE-ECDSA-AES128-GCM-SHA256",
        "ECDHE-ECDSA-AES128-SHA",
        "ECDHE-ECDSA-AES128-SHA256",
        "ECDHE-ECDSA-AES256-GCM-SHA384",
        "ECDHE-ECDSA-AES256-SHA",
        "ECDHE-ECDSA-AES256-SHA384",
        "ECDHE-RSA-AES128-GCM-SHA256",
        "ECDHE-RSA-AES128-SHA",
        "ECDHE-RSA-AES128-SHA256",
        "ECDHE-RSA-AES256-GCM-SHA384",
        "ECDHE-RSA-AES256-SHA",
        "ECDHE-RSA-AES256-SHA384"
      ],
      "type": "SSLNegotiationPolicyType",
      "server_defined_cipher_order": True,
      "protocols": {
        "tlsv1": True,
        "tlsv1_1": True,
        "tlsv1_2": True,
        "sslv3": True,
        "sslv2": False
      }
    }
  },
  "Region": "us-east-1",
  "Scheme": "internet-facing",
  "SecurityGroups": [
    "sg-12345678"
  ],
  "SourceSecurityGroup": {
    "OwnerAlias": "012345678901",
    "GroupName": "MySG"
  },
  "Subnets": [
    "subnet-19999999"
  ],
  "Tags": [
    {
      "Value": "arn:aws:cloudformation:us-east-1:012345678901:stack/STACK/xxxxxxxxxxxxxxxxxxx",
      "Key": "aws:cloudformation:stack-id"
    }
  ],
  "VPCId": "vpc-49999999",
  "_version": 2
}

INTERNET_SG = {
    'id': 'sg-12345678',
    'name': 'INTERNETSG',
    'rules': [
        {
            'cidr_ip': '0.0.0.0/0',
            'rule_type': 'ingress'
        }
    ]
}

INTERNAL_SG = {
    'id': 'sg-87654321',
    'name': 'INTERNALSG',
    'rules': [
        {
            'cidr_ip': '10.0.0.0/8',
            'rule_type': 'ingress'
        }
    ]
}


class ELBTestCase(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        account_type_result = AccountType(name='AWS')
        db.session.add(account_type_result)
        db.session.commit()

        account = Account(identifier="012345678910", name="TEST_ACCOUNT",
                          account_type_id=account_type_result.id, notes="TEST_ACCOUNT",
                          third_party=False, active=True)

        db.session.add(account)
        db.session.commit()

    def test_check_internet_scheme_internet(self):
        # internet-facing
        # 0.0.0.0/0
        from security_monkey.auditors.elb import ELBAuditor
        auditor = ELBAuditor(accounts=["012345678910"])

        from security_monkey.cloudaux_watcher import CloudAuxChangeItem
        item = CloudAuxChangeItem(index='elb', account='TEST_ACCOUNT', name='MyELB', 
            arn="arn:aws:elasticloadbalancing:us-east-1:012345678910:loadbalancer/MyELB", config=INTERNET_ELB)

        def mock_get_watcher_support_items(*args, **kwargs):
            from security_monkey.watchers.security_group import SecurityGroupItem
            sg_item = SecurityGroupItem(region='us-east-1', account='TEST_ACCOUNT', name='INTERNETSG', config=INTERNET_SG)
            return [sg_item]

        auditor.get_watcher_support_items = mock_get_watcher_support_items

        auditor.check_internet_scheme(item)

        self.assertEqual(len(item.audit_issues), 1)
        issue = item.audit_issues[0]
        self.assertEqual(issue.issue, 'VPC ELB is Internet accessible.')
        self.assertEqual(issue.notes, 'SG [INTERNETSG] via [0.0.0.0/0]')

    def test_check_internet_scheme_internet_2(self):
        # internet-facing
        # 10.0.0.0/8
        from security_monkey.auditors.elb import ELBAuditor
        auditor = ELBAuditor(accounts=["012345678910"])

        from security_monkey.cloudaux_watcher import CloudAuxChangeItem
        item = CloudAuxChangeItem(index='elb', account='TEST_ACCOUNT', name='MyELB', 
            arn="arn:aws:elasticloadbalancing:us-east-1:012345678910:loadbalancer/MyELB", config=INTERNET_ELB)

        def mock_get_watcher_support_items(*args, **kwargs):
            from security_monkey.watchers.security_group import SecurityGroupItem
            sg_item = SecurityGroupItem(region='us-east-1', account='TEST_ACCOUNT', name='INTERNETSG', config=INTERNAL_SG)
            return [sg_item]

        auditor.get_watcher_support_items = mock_get_watcher_support_items

        auditor.check_internet_scheme(item)

        self.assertEqual(len(item.audit_issues), 0)

    def test_check_internet_scheme_internal(self):
        # internal
        # 10.0.0.0/8
        from security_monkey.auditors.elb import ELBAuditor
        auditor = ELBAuditor(accounts=["012345678910"])

        INTERNAL_ELB = dict(INTERNET_ELB)
        INTERNAL_ELB['Scheme'] = 'internal'

        from security_monkey.cloudaux_watcher import CloudAuxChangeItem
        item = CloudAuxChangeItem(index='elb', account='TEST_ACCOUNT', name='MyELB', 
            arn="arn:aws:elasticloadbalancing:us-east-1:012345678910:loadbalancer/MyELB", config=INTERNAL_ELB)

        def mock_get_watcher_support_items(*args, **kwargs):
            from security_monkey.watchers.security_group import SecurityGroupItem
            sg_item = SecurityGroupItem(region='us-east-1', account='TEST_ACCOUNT', name='INTERNETSG', config=INTERNAL_SG)
            return [sg_item]

        auditor.get_watcher_support_items = mock_get_watcher_support_items

        auditor.check_internet_scheme(item)

        self.assertEqual(len(item.audit_issues), 0)

    def test_check_internet_scheme_internal_2(self):
        # internal
        # 0.0.0.0/0
        from security_monkey.auditors.elb import ELBAuditor
        auditor = ELBAuditor(accounts=["012345678910"])

        INTERNAL_ELB = dict(INTERNET_ELB)
        INTERNAL_ELB['Scheme'] = 'internal'

        from security_monkey.cloudaux_watcher import CloudAuxChangeItem
        item = CloudAuxChangeItem(index='elb', account='TEST_ACCOUNT', name='MyELB', 
            arn="arn:aws:elasticloadbalancing:us-east-1:012345678910:loadbalancer/MyELB", config=INTERNAL_ELB)

        def mock_get_watcher_support_items(*args, **kwargs):
            from security_monkey.watchers.security_group import SecurityGroupItem
            sg_item = SecurityGroupItem(region='us-east-1', account='TEST_ACCOUNT', name='INTERNETSG', config=INTERNET_SG)
            return [sg_item]

        auditor.get_watcher_support_items = mock_get_watcher_support_items

        auditor.check_internet_scheme(item)

        self.assertEqual(len(item.audit_issues), 0)

    def test_process_reference_policy(self):
        from security_monkey.auditors.elb import ELBAuditor
        auditor = ELBAuditor(accounts=["012345678910"])

        from security_monkey.cloudaux_watcher import CloudAuxChangeItem
        item = CloudAuxChangeItem(index='elb', account='TEST_ACCOUNT', name='MyELB', 
            arn="arn:aws:elasticloadbalancing:us-east-1:012345678910:loadbalancer/MyELB", config=INTERNET_ELB)

        auditor._process_reference_policy(None, 'MyCustomPolicy', '443', item)
        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].issue, 'Custom listener policies are discouraged.')

        item.audit_issues = list()
        auditor._process_reference_policy('ELBSecurityPolicy-2011-08', 'MyCustomPolicy', '443', item)
        self.assertEqual(len(item.audit_issues), 5)
        issues = [issue.issue for issue in item.audit_issues]
        self.assertIn("ELBSecurityPolicy-2011-08 is vulnerable and deprecated", issues)
        self.assertIn("ELBSecurityPolicy-2011-08 is vulnerable to poodlebleed", issues)
        self.assertIn("ELBSecurityPolicy-2011-08 lacks server order cipher preference.", issues)
        self.assertIn("ELBSecurityPolicy-2011-08 contains RC4 ciphers (RC4-SHA) that have been removed in newer policies.", issues)
        self.assertIn("ELBSecurityPolicy-2011-08 contains a weaker cipher (DES-CBC3-SHA) "
                           "for backwards compatibility with Windows XP systems. Vulnerable to SWEET32 CVE-2016-2183.", issues)

        item.audit_issues = list()
        auditor._process_reference_policy('ELBSecurityPolicy-2014-01', 'MyCustomPolicy', '443', item)
        self.assertEqual(len(item.audit_issues), 3)

        item.audit_issues = list()
        auditor._process_reference_policy('ELBSecurityPolicy-2014-10', 'MyCustomPolicy', '443', item)
        self.assertEqual(len(item.audit_issues), 2)

        item.audit_issues = list()
        auditor._process_reference_policy('ELBSecurityPolicy-2015-02', 'MyCustomPolicy', '443', item)
        self.assertEqual(len(item.audit_issues), 2)

        item.audit_issues = list()
        auditor._process_reference_policy('ELBSecurityPolicy-2015-03', 'MyCustomPolicy', '443', item)
        self.assertEqual(len(item.audit_issues), 2)

        item.audit_issues = list()
        auditor._process_reference_policy('ELBSecurityPolicy-2015-05', 'MyCustomPolicy', '443', item)
        self.assertEqual(len(item.audit_issues), 1)

        item.audit_issues = list()
        auditor._process_reference_policy('ELBSecurityPolicy-2016-08', 'MyCustomPolicy', '443', item)
        self.assertEqual(len(item.audit_issues), 0)

        item.audit_issues = list()
        auditor._process_reference_policy('ELBSecurityPolicy-TLS-1-1-2017-01', 'MyCustomPolicy', '443', item)
        self.assertEqual(len(item.audit_issues), 0)

        item.audit_issues = list()
        auditor._process_reference_policy('ELBSecurityPolicy-TLS-1-2-2017-01', 'MyCustomPolicy', '443', item)
        self.assertEqual(len(item.audit_issues), 0)

        item.audit_issues = list()
        auditor._process_reference_policy('OTHER_REFERENCE_POLICY', 'MyCustomPolicy', '443', item)
        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].issue, 'Unknown reference policy.')

    def test_process_custom_listener_policy(self):
        from security_monkey.auditors.elb import ELBAuditor
        auditor = ELBAuditor(accounts=["012345678910"])

        from security_monkey.cloudaux_watcher import CloudAuxChangeItem
        item = CloudAuxChangeItem(index='elb', account='TEST_ACCOUNT', name='MyELB', 
            arn="arn:aws:elasticloadbalancing:us-east-1:012345678910:loadbalancer/MyELB", config=INTERNET_ELB)

        # We'll just modify it and pretend it's a custom policy
        policy = dict(INTERNET_ELB['PolicyDescriptions']['ELBSecurityPolicy-2016-08'])

        auditor._process_custom_listener_policy('ELBSecurityPolicy-2016-08', policy, '443', item)
        self.assertEqual(len(item.audit_issues), 1)

        item.audit_issues = list()
        policy['protocols']['sslv2'] = True
        auditor._process_custom_listener_policy('ELBSecurityPolicy-2016-08', policy, '443', item)
        self.assertEqual(len(item.audit_issues), 2)

        item.audit_issues = list()
        policy['server_defined_cipher_order'] = False
        auditor._process_custom_listener_policy('ELBSecurityPolicy-2016-08', policy, '443', item)
        self.assertEqual(len(item.audit_issues), 3)

        # simulate export grade
        item.audit_issues = list()
        policy['supported_ciphers'].append('EXP-RC4-MD5')
        auditor._process_custom_listener_policy('ELBSecurityPolicy-2016-08', policy, '443', item)
        self.assertEqual(len(item.audit_issues), 4)

        # simulate deprecated cipher 
        item.audit_issues = list()
        policy['supported_ciphers'].append('RC2-CBC-MD5')
        auditor._process_custom_listener_policy('ELBSecurityPolicy-2016-08', policy, '443', item)
        self.assertEqual(len(item.audit_issues), 5)

        # simulate not-recommended cipher
        item.audit_issues = list()
        policy['supported_ciphers'].append('CAMELLIA128-SHA')
        auditor._process_custom_listener_policy('ELBSecurityPolicy-2016-08', policy, '443', item)
        self.assertEqual(len(item.audit_issues), 6)

    def test_check_listener_reference_policy(self):
        from security_monkey.auditors.elb import ELBAuditor
        auditor = ELBAuditor(accounts=["012345678910"])

        from security_monkey.cloudaux_watcher import CloudAuxChangeItem
        item = CloudAuxChangeItem(index='elb', account='TEST_ACCOUNT', name='MyELB', 
            arn="arn:aws:elasticloadbalancing:us-east-1:012345678910:loadbalancer/MyELB", config=INTERNET_ELB)

        auditor.check_listener_reference_policy(item)
        self.assertEqual(len(item.audit_issues), 0)

    def test_check_logging(self):
        from security_monkey.auditors.elb import ELBAuditor
        auditor = ELBAuditor(accounts=["012345678910"])

        from security_monkey.cloudaux_watcher import CloudAuxChangeItem
        item = CloudAuxChangeItem(index='elb', account='TEST_ACCOUNT', name='MyELB', 
            arn="arn:aws:elasticloadbalancing:us-east-1:012345678910:loadbalancer/MyELB", config=INTERNET_ELB)

        auditor.check_logging(item)
        self.assertEqual(len(item.audit_issues), 0)

        elb = dict(INTERNET_ELB)
        elb['Attributes']['AccessLog']['Enabled'] = False
        item = CloudAuxChangeItem(index='elb', account='TEST_ACCOUNT', name='MyELB', 
            arn="arn:aws:elasticloadbalancing:us-east-1:012345678910:loadbalancer/MyELB", config=INTERNET_ELB)

        auditor.check_logging(item)
        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].issue, 'ELB is not configured for logging.')

        del elb['Attributes']['AccessLog']
        item = CloudAuxChangeItem(index='elb', account='TEST_ACCOUNT', name='MyELB', 
            arn="arn:aws:elasticloadbalancing:us-east-1:012345678910:loadbalancer/MyELB", config=INTERNET_ELB)

        auditor.check_logging(item)
        self.assertEqual(len(item.audit_issues), 1)
        self.assertEqual(item.audit_issues[0].issue, 'ELB is not configured for logging.')