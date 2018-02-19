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

from security_monkey.decorators import record_exception
from security_monkey.decorators import iter_account_region
from security_monkey.watcher import Watcher, ChangeItem
from security_monkey.datastore import Account
from security_monkey import app, ARN_PREFIX


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

        @iter_account_region(index=self.index, accounts=self.accounts, service_name='es')
        def slurp_items(**kwargs):
            item_list = []
            exception_map = {}
            kwargs['exception_map'] = exception_map

            account_db = Account.query.filter(Account.name == kwargs['account_name']).first()
            account_num = account_db.identifier

            es_info = self.get_all_es_domains_in_region(**kwargs)
            if es_info is None:
                return item_list, exception_map
            (client, domains) = es_info

            app.logger.debug("Found {} {}".format(len(domains), ElasticSearchService.i_am_plural))
            for domain in domains:
                if self.check_ignore_list(domain["DomainName"]):
                    continue

                # Fetch the policy:
                item = self.build_item(domain["DomainName"], client, account_num, **kwargs)

                if item:
                    item_list.append(item)

            return item_list, exception_map
        return slurp_items()

    @record_exception(source='{index}-watcher'.format(index=index), pop_exception_fields=False)
    def get_all_es_domains_in_region(self, **kwargs):
        from security_monkey.common.sts_connect import connect
        client = connect(kwargs['account_name'], "boto3.es.client", region=kwargs['region'])
        app.logger.debug("Checking {}/{}/{}".format(ElasticSearchService.index, kwargs['account_name'], kwargs['region']))
        # No need to paginate according to: client.can_paginate("list_domain_names")
        domains = self.wrap_aws_rate_limited_call(client.list_domain_names)["DomainNames"]

        return client, domains

    @record_exception(source='{index}-watcher'.format(index=index), pop_exception_fields=False)
    def build_item(self, domain, client, account_num, **kwargs):
        arn = ARN_PREFIX + ':es:{region}:{account_number}:domain/{domain_name}'.format(
            region=kwargs['region'],
            account_number=account_num,
            domain_name=domain)

        config = {
            'arn': arn
        }

        domain_config = self.wrap_aws_rate_limited_call(client.describe_elasticsearch_domain_config,
                                                        DomainName=domain)
        # Does the cluster have a policy?
        if domain_config["DomainConfig"]["AccessPolicies"]["Options"] == "":
            config['policy'] = {}
        else:
            config['policy'] = json.loads(domain_config["DomainConfig"]["AccessPolicies"]["Options"])
        config['name'] = domain

        return ElasticSearchServiceItem(region=kwargs['region'], account=kwargs['account_name'], name=domain, arn=arn,
                                        config=config, source_watcher=self)


class ElasticSearchServiceItem(ChangeItem):
    def __init__(self, region=None, account=None, name=None, arn=None, config=None, source_watcher=None):
        super(ElasticSearchServiceItem, self).__init__(
            index=ElasticSearchService.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config if config else {},
            source_watcher=source_watcher)
