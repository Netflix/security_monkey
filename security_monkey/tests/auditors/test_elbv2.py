from security_monkey.datastore import Account, AccountType
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey import db, AWS_DEFAULT_REGION, ARN_PREFIX


class ELBv2TestCase(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        pass

    def test_check_internet_facing(self):
        # internet-facing
        # 0.0.0.0/0
        from security_monkey.auditors.elbv2 import ELBv2Auditor
        auditor = ELBv2Auditor(accounts=["012345678910"])
        
        alb = {
            'Scheme': 'internet-facing',
            'SecurityGroups': ['sg-12345678'],
            'Listeners': [
                {
                    'Protocol': "HTTP",
                    'Port': 80
                }]
        }

        from security_monkey.cloudaux_watcher import CloudAuxChangeItem
        item = CloudAuxChangeItem(
            index='alb',
            account='TEST_ACCOUNT',
            name='MyELB', 
            arn=ARN_PREFIX + ":elasticloadbalancing:" + AWS_DEFAULT_REGION + ":012345678910:loadbalancer/MyELB",
            config=alb)

        def mock_get_auditor_support_items(*args, **kwargs):
            class MockIngressIssue:
                issue = 'Internet Accessible'
                notes = 'Entity: [cidr:0.0.0.0/0] Access: [ingress:tcp:80]'
                score = 10
            
            class MockIngressAllProtocolsIssue(MockIngressIssue):
                notes = 'Entity: [cidr:0.0.0.0/0] Access: [ingress:all_protocols:all_ports]'

            class MockIngressPortRangeIssue(MockIngressIssue):
                notes = 'Entity: [cidr:0.0.0.0/0] Access: [ingress:tcp:77-1023]'

            class MockEgressIssue(MockIngressIssue):
                notes = 'Entity: [cidr:0.0.0.0/0] Access: [egress:tcp:80]'

            class MockPortNotListenerPortIssue(MockIngressIssue):
                notes = 'Entity: [cidr:0.0.0.0/0] Access: [ingress:tcp:66555]'

            class MockNonConformingIssue(MockIngressIssue):
                notes = 'Some random rule.'

            class DBItem:
                issues = list()

            from security_monkey.watchers.security_group import SecurityGroupItem
            sg_item = SecurityGroupItem(
                region=AWS_DEFAULT_REGION,
                account='TEST_ACCOUNT',
                name='INTERNETSG',
                config={
                    'id': 'sg-12345678',
                    'name': 'INTERNETSG',
                    'rules': [
                        {
                            'cidr_ip': '0.0.0.0/0',
                            'rule_type': 'ingress',
                            'port': 80
                        }
                    ]
                })

            sg_item.db_item = DBItem()
            sg_item.db_item.issues = [
                MockIngressIssue(), MockIngressAllProtocolsIssue(), MockEgressIssue(),
                MockNonConformingIssue(), MockPortNotListenerPortIssue(),
                MockIngressPortRangeIssue()]
            return [sg_item]

        def mock_link_to_support_item_issues(item, sg, sub_issue_message, score):
            auditor.add_issue(score, sub_issue_message, item, notes='Related to: INTERNETSG (sg-12345678 in vpc-49999999)')

        auditor.get_auditor_support_items = mock_get_auditor_support_items
        auditor.link_to_support_item_issues = mock_link_to_support_item_issues

        auditor.check_internet_facing(item)

        self.assertEqual(len(item.audit_issues), 1)
        issue = item.audit_issues[0]
        self.assertEqual(issue.issue, 'Internet Accessible')
        self.assertEqual(issue.notes, 'Related to: INTERNETSG (sg-12345678 in vpc-49999999)')


    def test_check_logging(self):
        from security_monkey.auditors.elbv2 import ELBv2Auditor
        auditor = ELBv2Auditor(accounts=['012345678910'])

        alb = {
            'Attributes': [{
                'Key': 'access_logs.s3.enabled',
                'Value': 'false'
            }]}

        from security_monkey.cloudaux_watcher import CloudAuxChangeItem
        item = CloudAuxChangeItem(
            index='alb',
            account='TEST_ACCOUNT',
            name='MyALB', 
            arn=ARN_PREFIX + ":elasticloadbalancing:" + AWS_DEFAULT_REGION + ":012345678910:loadbalancer/app/MyALB/7f734113942",
            config=alb)

        auditor.check_logging(item)
        self.assertEqual(len(item.audit_issues), 1)
        issue = item.audit_issues[0]
        self.assertEqual(issue.issue, 'Recommendation')
        self.assertEqual(issue.notes, 'Enable access logs')

    def test_check_deletion_protection(self):
        from security_monkey.auditors.elbv2 import ELBv2Auditor
        auditor = ELBv2Auditor(accounts=['012345678910'])

        alb = {
            'Attributes': [{
                'Key': 'deletion_protection.enabled',
                'Value': 'false'
            }]}

        from security_monkey.cloudaux_watcher import CloudAuxChangeItem
        item = CloudAuxChangeItem(
            index='alb',
            account='TEST_ACCOUNT',
            name='MyALB', 
            arn=ARN_PREFIX + ":elasticloadbalancing:" + AWS_DEFAULT_REGION + ":012345678910:loadbalancer/app/MyALB/7f734113942",
            config=alb)

        auditor.check_deletion_protection(item)
        self.assertEqual(len(item.audit_issues), 1)
        issue = item.audit_issues[0]
        self.assertEqual(issue.issue, 'Recommendation')
        self.assertEqual(issue.notes,  'Enable deletion protection')

    def test_check_ssl_policy_no_policy(self):
        from security_monkey.auditors.elbv2 import ELBv2Auditor
        auditor = ELBv2Auditor(accounts=['012345678910'])

        alb = {
            'Listeners': [{
                'Port': 80,
                'SslPolicy': None
            }]}
            

        from security_monkey.cloudaux_watcher import CloudAuxChangeItem
        item = CloudAuxChangeItem(
            index='alb',
            account='TEST_ACCOUNT',
            name='MyALB', 
            arn=ARN_PREFIX + ":elasticloadbalancing:" + AWS_DEFAULT_REGION + ":012345678910:loadbalancer/app/MyALB/7f734113942",
            config=alb)

        auditor.check_ssl_policy(item)
        self.assertEqual(len(item.audit_issues), 0)

        item.new_config = {
            'Listeners': [{
                'Port': 443,
                'SslPolicy': 'ELBSecurityPolicy-TLS-1-0-2015-04'
            }]}

        auditor.check_ssl_policy(item)
        self.assertEqual(len(item.audit_issues), 1)
        issue = item.audit_issues[0]
        self.assertEqual(issue.issue, 'Insecure TLS')
        self.assertEqual(issue.notes, 'Policy: [ELBSecurityPolicy-TLS-1-0-2015-04] Port: [443] Reason: [Weak cipher (DES-CBC3-SHA) for Windows XP support] CVE: [SWEET32 CVE-2016-2183]')

        item.audit_issues = []
        item.new_config = {
            'Listeners': [{
                'Port': 443,
                'SslPolicy': 'ELBSecurityPolicy-DoesntExist'
            }]}

        auditor.check_ssl_policy(item)
        self.assertEqual(len(item.audit_issues), 1)
        issue = item.audit_issues[0]
        self.assertEqual(issue.issue, 'Insecure TLS')
        self.assertEqual(issue.notes, 'Policy: [ELBSecurityPolicy-DoesntExist] Port: [443] Reason: [Unknown reference policy]')