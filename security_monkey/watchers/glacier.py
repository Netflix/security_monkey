#     Copyright 2017 Netflix
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
.. module: security_monkey.watchers.glacier
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Travis McPeak <tmcpeak@netflix.com> @travismcpeak

"""

from security_monkey.cloudaux_watcher import CloudAuxWatcher

from cloudaux.aws.glacier import list_vaults
from cloudaux.orchestration.aws.glacier import get_vault


class GlacierVault(CloudAuxWatcher):
    index = 'glacier'
    i_am_singular = 'Glacier Vault'
    i_am_plural = 'Glacier Vaults'

    def __init__(self, **kwargs):
        super(GlacierVault, self).__init__(**kwargs)
        self.honor_ephemerals = True
        self.ephemeral_paths = ['LastInventoryDate', 'NumberOfArchives', 'SizeInBytes']

    def get_name_from_list_output(self, item):
        return item['VaultName']

    def list_method(self, **kwargs):
        return list_vaults(**kwargs)

    def get_method(self, item, **kwargs):
        return get_vault(dict(item), **kwargs)
