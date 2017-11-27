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
.. module: security_monkey.tests.watchers.openstack.test_floating_ip
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Michael Stair <mstair@att.com>

"""
from security_monkey.tests.watchers.openstack import OpenStackWatcherTestCase

class OpenStackFloatingIPWatcherTestCase(OpenStackWatcherTestCase):

    def pre_test_setup(self):
        super(OpenStackFloatingIPWatcherTestCase, self).pre_test_setup()
        from security_monkey.watchers.openstack.network.openstack_floating_ip import OpenStackFloatingIP
        self.watcher = OpenStackFloatingIP(accounts=[self.account.name])
