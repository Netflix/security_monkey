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
.. module: security_monkey.openstack.watchers.object_container
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Michael Stair <mstair@att.com>

"""
from security_monkey.watchers.openstack.openstack_watcher import OpenStackWatcher
from cloudaux.openstack.object_container import get_container_metadata


class OpenStackObjectContainer(OpenStackWatcher):
    index = 'openstack_objectcontainer'
    i_am_singular = 'Object Container'
    i_am_plural = 'Object Containers'
    account_type = 'OpenStack'

    def __init__(self, *args, **kwargs):
        super(OpenStackObjectContainer, self).__init__(*args, **kwargs)
        self.ephemeral_paths = ["last_modified"]
        self.item_type = 'objectcontainer'
        self.service = 'object_store'
        self.generator = 'containers'

    """ one of few OpenStack configs that cannot have duplicate names in the tenant (and also doesn't
                really have an uuid """
    def get_name_from_list_output(self, item):
        return item.name

    def get_method(self, item, **kwargs):
        kwargs['container'] = item
        result = get_container_metadata(**kwargs)
        return super(OpenStackObjectContainer, self).get_method(result, **kwargs)
