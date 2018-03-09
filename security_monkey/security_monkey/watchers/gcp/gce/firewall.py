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
.. module: security_monkey.watchers.gcp.gce.firewall
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Tom Melendez <supertom@google.com> @supertom
"""
from security_monkey.common.gcp.util import get_gcp_project_creds, get_user_agent, gcp_resource_id_builder, modify
from security_monkey.decorators import record_exception
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem

from cloudaux.gcp.decorators import iter_project
from cloudaux.gcp.gce.firewall import list_firewall_rules


class GCEFirewallRule(Watcher):
    index = 'gcefirewallrule'
    i_am_singular = 'GCEFirewallRule'
    i_am_plural = 'GCEFirewallRules'
    account_type = 'GCP'

    def __init__(self, accounts=None, debug=False):
        super(GCEFirewallRule, self).__init__(accounts=accounts, debug=debug)
        self.honor_ephemerals = True
        self.ephemeral_paths = [
            "Etag",
        ]
        self.user_agent = get_user_agent()

    @record_exception()
    def slurp(self):
        """
        :returns: item_list - list of GCEFirewallRules.
        :returns: exception _map - A dict where the keys are a tuple containing the
        location of the exception and the value is the actual exception
        """
        self.prep_for_slurp()
        project_creds = get_gcp_project_creds(self.accounts)

        @iter_project(projects=project_creds)
        def slurp_items(**kwargs):
            item_list = []
            kwargs['user_agent'] = self.user_agent
            rules = list_firewall_rules(**kwargs)

            for rule in rules:
                resource_id = gcp_resource_id_builder(
                    kwargs['project'], 'compute.firewall.get', rule['name'])
                item_list.append(
                    GCEFirewallRuleItem(
                        region='global',
                        # This should only ever be the first item (shouldn't make this a list)
                        account=self.accounts[0],
                        name=rule['name'],
                        arn=resource_id,
                        config=modify(rule, output='camelized'),
                        source_watcher=self))
            return item_list, kwargs.get('exception_map', {})

        return slurp_items()


class GCEFirewallRuleItem(ChangeItem):

    def __init__(self,
                 region=None,
                 account=None,
                 name=None,
                 arn=None,
                 config=None,
                 source_watcher=None):
        super(GCEFirewallRuleItem, self).__init__(
            index=GCEFirewallRule.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config if config else {},
            source_watcher=source_watcher)
