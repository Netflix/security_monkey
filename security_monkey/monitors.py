"""
.. module: security_monkey.monitors
    :platform: Unix
    :synopsis: Monitors are a grouping of a watcher and it's associated auditor

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.watchers.sns import SNS
from security_monkey.auditors.sns import SNSAuditor
from security_monkey.watchers.sqs import SQS
from security_monkey.watchers.keypair import Keypair
from security_monkey.watchers.iam_role import IAMRole
from security_monkey.auditors.iam_role import IAMRoleAuditor
from security_monkey.watchers.iam_group import IAMGroup
from security_monkey.auditors.iam_group import IAMGroupAuditor
from security_monkey.watchers.iam_user import IAMUser
from security_monkey.auditors.iam_user import IAMUserAuditor
from security_monkey.watchers.security_group import SecurityGroup
from security_monkey.auditors.security_group import SecurityGroupAuditor
from security_monkey.watchers.rds_security_group import RDSSecurityGroup
from security_monkey.auditors.rds_security_group import RDSSecurityGroupAuditor
from security_monkey.watchers.s3 import S3
from security_monkey.auditors.s3 import S3Auditor
from security_monkey.watchers.elb import ELB
from security_monkey.auditors.elb import ELBAuditor
from security_monkey.watchers.iam_ssl import IAMSSL
from security_monkey.auditors.iam_ssl import IAMSSLAuditor
from security_monkey.watchers.redshift import Redshift
from security_monkey.auditors.redshift import RedshiftAuditor
from security_monkey.watchers.elastic_ip import ElasticIP
from security_monkey.watchers.ses import SES
from security_monkey.auditors.ses import SESAuditor
from security_monkey.watchers.vpc.vpc import VPC


class Monitor(object):
    """Collects a watcher with the associated auditor"""
    def __init__(self, index, watcher_class, auditor_class=None):
        self.index = index
        self.watcher_class = watcher_class
        self.auditor_class = auditor_class

    def has_auditor(self):
        return self.auditor_class is not None


__MONITORS = {
    SQS.index:
        Monitor(SQS.index, SQS, None),
    ELB.index:
        Monitor(ELB.index, ELB, ELBAuditor),
    IAMSSL.index:
        Monitor(IAMSSL.index, IAMSSL, IAMSSLAuditor),
    RDSSecurityGroup.index:
        Monitor(RDSSecurityGroup.index, RDSSecurityGroup, RDSSecurityGroupAuditor),
    SecurityGroup.index:
        Monitor(SecurityGroup.index, SecurityGroup, SecurityGroupAuditor),
    S3.index:
        Monitor(S3.index, S3, S3Auditor),
    IAMUser.index:
        Monitor(IAMUser.index, IAMUser, IAMUserAuditor),
    IAMRole.index:
        Monitor(IAMRole.index, IAMRole, IAMRoleAuditor),
    IAMGroup.index:
        Monitor(IAMGroup.index, IAMGroup, IAMGroupAuditor),
    Keypair.index:
        Monitor(Keypair.index, Keypair, None),
    SNS.index:
        Monitor(SNS.index, SNS, SNSAuditor),
    Redshift.index:
        Monitor(Redshift.index, Redshift, RedshiftAuditor),
    ElasticIP.index:
        Monitor(ElasticIP.index, ElasticIP, None),
    SES.index:
        Monitor(SES.index, SES, SESAuditor),
    VPC.index:
        Monitor(VPC.index, VPC, None)
}


def get_monitor(monitor_name):
    return __MONITORS.get(monitor_name)


def all_monitors():
    return __MONITORS.itervalues()
