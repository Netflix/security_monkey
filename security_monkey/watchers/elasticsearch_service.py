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
from security_monkey.datastore import Account
from security_monkey import app

import boto3


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
            account_db = Account.query.filter(Account.name == account).first()
            account_number = account_db.identifier

            for region in boto3.session.Session().get_available_regions(service_name="es"):
                try:
                    if region in TROUBLE_REGIONS:
                        continue

                    (client, domains) = self.get_all_es_domains_in_region(account, region)
                except Exception as e:
                    if region not in TROUBLE_REGIONS:
                        exc = BotoConnectionIssue(str(e), self.index, account, region)
                        self.slurp_exception((self.index, account, region), exc, exception_map,
                                             source="{}-watcher".format(self.index))
                    continue

                app.logger.debug("Found {} {}".format(len(domains), ElasticSearchService.i_am_plural))
                for domain in domains:
                    if self.check_ignore_list(domain["DomainName"]):
                        continue

                    # Fetch the policy:
                    item = self.build_item(domain["DomainName"], client, region, account, account_number,
                                           exception_map)
                    if item:
                        item_list.append(item)

        return item_list, exception_map

    def get_all_es_domains_in_region(self, account, region):
        from security_monkey.common.sts_connect import connect
        client = connect(account, "boto3.es.client", region=region)
        app.logger.debug("Checking {}/{}/{}".format(ElasticSearchService.index, account, region))
        # No need to paginate according to: client.can_paginate("list_domain_names")
        domains = self.wrap_aws_rate_limited_call(client.list_domain_names)["DomainNames"]

        return client, domains

    def build_item(self, domain, client, region, account, account_number, exception_map):
        arn = 'arn:aws:es:{region}:{account_number}:domain/{domain_name}'.format(
            region=region,
            account_number=account_number,
            domain_name=domain)

        config = {
            'arn': arn
        }

        try:
            domain_config = self.wrap_aws_rate_limited_call(client.describe_elasticsearch_domain_config,
                                                            DomainName=domain)
            # Does the cluster have a policy?
            if domain_config["DomainConfig"]["AccessPolicies"]["Options"] == "":
                config['policy'] = {}
            else:
                config['policy'] = json.loads(domain_config["DomainConfig"]["AccessPolicies"]["Options"])
            config['name'] = domain

        except Exception as e:
            self.slurp_exception((domain, account, region), e, exception_map, source="{}-watcher".format(self.index))
            return None

        return ElasticSearchServiceItem(region=region, account=account, name=domain, arn=arn, config=config)


class ElasticSearchServiceItem(ChangeItem):
    def __init__(self, region=None, account=None, name=None, arn=None, config={}):
        super(ElasticSearchServiceItem, self).__init__(
            index=ElasticSearchService.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config)
