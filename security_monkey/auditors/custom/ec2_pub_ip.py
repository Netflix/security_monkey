"""
.. module: security_monkey.auditors.ec2_pub_ip
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Damian Johnstone <djohnstone@deputy.com>

"""
from security_monkey.auditor import Auditor
from security_monkey.watchers.ec2.ec2_instance import EC2Instance


class EC2PubIPAuditor(Auditor):
    index = EC2Instance.index
    i_am_singular = EC2Instance.i_am_singular
    i_am_plural = EC2Instance.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(EC2PubIPAuditor, self).__init__(accounts=accounts, debug=debug)


    def check_public_ip(self, ec2_item):
        """
        alert when an instance has a public IP address
        """
        if ec2_item.config.get('public_ip_address', []) is not None:
            self.add_issue(10, 'EC2 Instance has public IP.', ec2_item)
