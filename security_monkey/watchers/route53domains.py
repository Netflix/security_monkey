#     Copyright 2016 Bridgewater Associates
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
.. module: security_monkey.watchers.route53domains
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.decorators import record_exception
from security_monkey.decorators import iter_account_region
from security_monkey import app


class Route53Domains(Watcher):
    index = 'route53domains'
    i_am_singular = 'Route 53 Domain'
    i_am_plural = 'Route 53 Domains'

    def __init__(self, accounts=None, debug=False):
        super(Route53Domains, self).__init__(accounts=accounts, debug=debug)

    @record_exception(source="route53domains-watcher")
    def connect(self, **kwargs):
        from security_monkey.common.sts_connect import connect
        return connect(kwargs['account_name'], 'boto3.route53domains.client',
                       region=kwargs['region'])

    @record_exception(source="route53domains-watcher")
    def list_domains(self, r53, **kwargs):
        marker = None
        domains = []
        while True:
            if marker:
                response = self.wrap_aws_rate_limited_call(
                    r53.list_domains(Marker=marker))
            else:
                response = self.wrap_aws_rate_limited_call(r53.list_domains)

            for domain in response.get('Domains'):
                domains.append(domain)

            if response.get('NextPageMarker'):
                marker = response.get('NextPageMarker')
            else:
                break

        return domains

    @record_exception(source="route53domains-watcher")
    def get_domain_detail(self, r53, domain_name, **kwargs):
        return r53.get_domain_detail(DomainName=domain_name)

    def slurp(self):
        """
        :returns: item_list - list of domain names.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception
        """
        self.prep_for_slurp()

        @iter_account_region(index=self.index, accounts=self.accounts,
                             service_name='route53domains')
        def slurp_items(**kwargs):
            app.logger.debug("Checking {}/{}/{}".format(Route53Domains.index,
                                                        kwargs['account_name'], kwargs['region']))
            item_list = []
            r53 = self.connect(**kwargs)
            if not r53:
                return item_list, kwargs['exception_map']

            domains = self.list_domains(r53, **kwargs)
            if not domains:
                return item_list, kwargs['exception_map']

            domain_list = []
            for domain in domains:
                domain_details = self.get_domain_detail(
                    r53, domain.get('DomainName'), **kwargs)

                if domain_details:
                    domain_list.append(domain_details)

            app.logger.debug("Found {} {}.".format(
                len(domain_list), self.i_am_plural))
            for domain in domain_list:
                name = domain['DomainName']

                if self.check_ignore_list(name):
                    continue

                item_config = {
                    'domain_name': name,
                    'admin_contact': domain['AdminContact'],
                    'registrant_contact': domain['RegistrantContact']
                }

                item = Route53DomainsItem(region=kwargs['region'],
                                          account=kwargs['account_name'],
                                          name=name, config=item_config, source_watcher=self)

                item_list.append(item)

            return item_list, kwargs['exception_map']
        return slurp_items()


class Route53DomainsItem(ChangeItem):

    def __init__(self, account=None, region=None, name=None, config=None, source_watcher=None):
        super(Route53DomainsItem, self).__init__(
            index=Route53Domains.index,
            region=region,
            account=account,
            name=name,
            new_config=config if config else {},
            source_watcher=source_watcher)
