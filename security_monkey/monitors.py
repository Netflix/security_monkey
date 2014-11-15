"""
.. module: security_monkey.monitors
    :platform: Unix
    :synopsis: Monitors are a grouping of a watcher and it's associated auditor

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from collections import namedtuple

from security_monkey.watchers.sns import SNS, SNSItem
from security_monkey.auditors.sns import SNSAuditor
from security_monkey.watchers.sqs import SQS
from security_monkey.watchers.keypair import Keypair
from security_monkey.watchers.iam_role import IAMRole, IAMRoleItem
from security_monkey.auditors.iam_role import IAMRoleAuditor
from security_monkey.watchers.iam_group import IAMGroup, IAMGroupItem
from security_monkey.auditors.iam_group import IAMGroupAuditor
from security_monkey.watchers.iam_user import IAMUser, IAMUserItem
from security_monkey.auditors.iam_user import IAMUserAuditor
from security_monkey.watchers.security_group import SecurityGroup, SecurityGroupItem
from security_monkey.auditors.security_group import SecurityGroupAuditor
from security_monkey.watchers.rds_security_group import RDSSecurityGroup, RDSSecurityGroupItem
from security_monkey.auditors.rds_security_group import RDSSecurityGroupAuditor
from security_monkey.watchers.s3 import S3, S3Item
from security_monkey.auditors.s3 import S3Auditor
from security_monkey.watchers.elb import ELB, ELBItem
from security_monkey.auditors.elb import ELBAuditor
from security_monkey.watchers.iam_ssl import IAMSSL
from security_monkey.watchers.redshift import Redshift, RedshiftCluster
from security_monkey.auditors.redshift import RedshiftAuditor
from security_monkey.watchers.elastic_ip import ElasticIP, ElasticIPItem

class Monitor(object):
    """Collects a watcher with the associated auditor"""
    def __init__(self, index, watcher_class, auditor_class=None, item_class=None):
        self.index = index
        self.watcher_class = watcher_class
        self.auditor_class = auditor_class
        self.item_class = item_class

    def has_auditor(self):
        return self.auditor_class is not None and self.item_class is not None


__MONITORS = {
    'sqs':      Monitor('sqs',      SQS,              None,                    None),
    'elb':      Monitor('elb',      ELB,              ELBAuditor,              ELBItem),
    'iamssl':   Monitor('iamssl',   IAMSSL,           None,                    None),
    'rds':      Monitor('rds',      RDSSecurityGroup, RDSSecurityGroupAuditor, RDSSecurityGroupItem),
    'sg':       Monitor('sg',       SecurityGroup,    SecurityGroupAuditor,    SecurityGroupItem),
    's3':       Monitor('s3',       S3,               S3Auditor,               S3Item),
    'iamuser':  Monitor('iamuser',  IAMUser,          IAMUserAuditor,          IAMUserItem),
    'iamrole':  Monitor('iamrole',  IAMRole,          IAMRoleAuditor,          IAMRoleItem),
    'iamgroup': Monitor('iamgroup', IAMGroup,         IAMGroupAuditor,         IAMGroupItem),
    'keypair':  Monitor('keypair',  Keypair,          None,                    None),
    'sns':      Monitor('sns',      SNS,              SNSAuditor,              SNSItem),
    'redshift': Monitor('redshift', Redshift,         RedshiftAuditor,         RedshiftCluster),
    'eip':      Monitor('eip',      ElasticIP,        None,                    ElasticIPItem)
}

def get_monitor(monitor_name):
    return __MONITORS.get(monitor_name)

def all_monitors():
    return __MONITORS.itervalues()
