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
.. module: security_monkey.openstack.watchers.security_group
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Michael Stair <mstair@att.com>

"""
from security_monkey.watchers.openstack.openstack_watcher import OpenStackWatcher
from security_monkey import app

from cloudaux.orchestration.openstack.security_group import get_security_group, FLAGS


class OpenStackSecurityGroup(OpenStackWatcher):
    index = 'openstack_securitygroup'
    i_am_singular = 'Security Group'
    i_am_plural = 'Security Groups'
    account_type = 'OpenStack'

    def __init__(self, *args, **kwargs):
        super(OpenStackSecurityGroup, self).__init__(*args, **kwargs)
        self.ephemeral_paths = ["assigned_to"]
        self.item_type = 'securitygroup'
        self.service = 'network'
        self.generator = 'security_groups'
        self.detail = app.config.get('SECURITYGROUP_INSTANCE_DETAIL', 'FULL')

    def get_method(self, item, **kwargs):
        result = super(OpenStackSecurityGroup, self).get_method(item, **kwargs)
        flags = FLAGS.RULES
        if not self.detail == 'NONE':
            kwargs['instance_detail'] = self.detail
            flags = flags | FLAGS.INSTANCES
        return get_security_group(result, flags=flags, **kwargs)
