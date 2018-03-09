#     Copyright 2017 Google, Inc.
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
.. module: security_monkey.watchers.gcp.gce.network
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Tom Melendez <supertom@google.com> @supertom

"""
from security_monkey.common.gcp.util import get_gcp_project_creds, get_user_agent, gcp_resource_id_builder
from security_monkey.decorators import record_exception
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem

from cloudaux.gcp.decorators import iter_project
from cloudaux.gcp.gce.network import list_networks
from cloudaux.orchestration.gcp.gce.network import get_network_and_subnetworks


class GCENetwork(Watcher):
    index = 'gcenetwork'
    i_am_singular = 'GCENetwork'
    i_am_plural = 'GCENetworks'
    account_type = 'GCP'

    def __init__(self, accounts=None, debug=False):
        super(GCENetwork, self).__init__(accounts=accounts, debug=debug)
        self.honor_ephemerals = True
        self.ephemeral_paths = [
            "Etag",
        ]
        self.user_agent = get_user_agent()

    @record_exception()
    def slurp(self):
        """
        :returns: item_list - list of GCENetwork.
        :returns: exception _map - A dict where the keys are a tuple containing the
        location of the exception and the value is the actual exception
        """
        self.prep_for_slurp()

        project_creds = get_gcp_project_creds(self.accounts)

        @iter_project(projects=project_creds)
        def slurp_items(**kwargs):
            item_list = []
            kwargs['user_agent'] = self.user_agent
            networks = list_networks(**kwargs)

            for network in networks:
                resource_id = gcp_resource_id_builder(
                    kwargs['project'], 'compute.network.get', network['name'])
                net_complete = get_network_and_subnetworks(
                    network['name'], **kwargs)
                item_list.append(
                    GCENetworkItem(
                        region='global',
                        # This should only ever be the first item (shouldn't make this a list)
                        account=self.accounts[0],
                        name=net_complete['Name'],
                        arn=resource_id,
                        config=net_complete,
                        source_watcher=self))
            return item_list, kwargs.get('exception_map', {})

        return slurp_items()


class GCENetworkItem(ChangeItem):

    def __init__(self,
                 region=None,
                 account=None,
                 name=None,
                 arn=None,
                 config=None,
                 source_watcher=None):
        super(GCENetworkItem, self).__init__(
            index=GCENetwork.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config if config else {},
            source_watcher=source_watcher)
