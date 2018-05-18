#     Copyright (c) 2017 AT&T Intellectual Property. All rights reserved.
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
.. module: security_monkey.openstack.auditors.security_group
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Michael Stair <mstair@att.com>

"""

from security_monkey.auditors.security_group import SecurityGroupAuditor
from security_monkey.watchers.openstack.network.openstack_security_group import OpenStackSecurityGroup

class OpenStackSecurityGroupAuditor(SecurityGroupAuditor):
    index = OpenStackSecurityGroup.index
    i_am_singular = OpenStackSecurityGroup.i_am_singular
    i_am_plural = OpenStackSecurityGroup.i_am_plural
    network_whitelist = []

    def __init__(self, accounts=None, debug=False):
        super(OpenStackSecurityGroupAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_securitygroup_ec2_rfc1918(self, sg_item):
        pass

    def _check_internet_cidr(self, cidr):
        ''' some public clouds default to none for any source '''
        return not cidr or super(OpenStackSecurityGroupAuditor, self)._check_internet_cidr(cidr)
