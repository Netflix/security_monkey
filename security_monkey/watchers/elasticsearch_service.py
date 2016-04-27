#     Copyright 2015 Netflix, Inc.
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
.. module: security_monkey.watchers.keypair
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Mike Grima <mgrima@netflix.com>

"""
import json

from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey.watcher import Watcher, ChangeItem
from security_monkey import app

from boto.ec2 import regions


class ElasticSearchService(Watcher):
    index = 'elasticsearchservice'
    i_am_singular = 'ElasticSearch Service Access Policy'
    i_am_plural = 'ElasticSearch Service Access Policies'

    def __init__(self, accounts=None, debug=False):
        super(ElasticSearchService, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        """
        :returns: item_list - list of ElasticSearchService Items
        :return:  exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()

        item_list = []
        exception_map = {}
        for account in self.accounts:
            for region in regions():
                try:
                    if region.name in TROUBLE_REGIONS:
                        continue

                    (client, domains) = self.get_all_es_domains_in_region(account, region)
                except Exception as e:
                    if region.name not in TROUBLE_REGIONS:
                        exc = BotoConnectionIssue(str(e), 'es', account, region.name)
                        self.slurp_exception((self.index, account, region.name), exc, exception_map)
                    continue

                app.logger.debug("Found {} {}".format(len(domains), ElasticSearchService.i_am_plural))
                for domain in domains:
                    if self.check_ignore_list(domain["DomainName"]):
                        continue

                    # Fetch the policy:
                    item = self.build_item(domain["DomainName"], client, region.name, account, exception_map)
                    if item:
                        item_list.append(item)

        return item_list, exception_map

    def get_all_es_domains_in_region(self, account, region):
        from security_monkey.common.sts_connect import connect
        client = connect(account, "es", region=region)
        app.logger.debug("Checking {}/{}/{}".format(ElasticSearchService.index, account, region.name))
        # No need to paginate according to: client.can_paginate("list_domain_names")
        domains = self.wrap_aws_rate_limited_call(client.list_domain_names)["DomainNames"]

        return client, domains

    def build_item(self, domain, client, region, account, exception_map):
        config = {}

        try:
            domain_config = self.wrap_aws_rate_limited_call(client.describe_elasticsearch_domain_config,
                                                            DomainName=domain)
            config['policy'] = json.loads(domain_config["DomainConfig"]["AccessPolicies"]["Options"])
            config['name'] = domain

        except Exception as e:
            self.slurp_exception((domain, client, region), e, exception_map)
            return None

        return ElasticSearchServiceItem(region=region, account=account, name=domain, config=config)


class ElasticSearchServiceItem(ChangeItem):
    def __init__(self, region=None, account=None, name=None, config={}):
        super(ElasticSearchServiceItem, self).__init__(
                index=ElasticSearchService.index,
                region=region,
                account=account,
                name=name,
                new_config=config
        )
