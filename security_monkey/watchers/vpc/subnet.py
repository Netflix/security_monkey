#     Copyright 2014 Netflix, Inc.
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
.. module: security_monkey.watchers.subnet
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.decorators import record_exception, iter_account_region
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey import app


class Subnet(Watcher):
    index = 'subnet'
    i_am_singular = 'Subnet'
    i_am_plural = 'Subnets'

    def __init__(self, accounts=None, debug=False):
        super(Subnet, self).__init__(accounts=accounts, debug=debug)

    @record_exception()
    def get_all_subnets(self, **kwargs):
        from security_monkey.common.sts_connect import connect
        conn = connect(kwargs['account_name'], 'vpc', region=kwargs['region'],
                       assumed_role=kwargs['assumed_role'])

        all_subnets = self.wrap_aws_rate_limited_call(conn.get_all_subnets)
        return all_subnets

    def slurp(self):
        """
        :returns: item_list - list of subnets.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()

        @iter_account_region(index=self.index, accounts=self.accounts, service_name='ec2')
        def slurp_items(**kwargs):
            item_list = []
            exception_map = {}
            kwargs['exception_map'] = exception_map
            app.logger.debug("Checking {}/{}/{}".format(self.index, kwargs['account_name'], kwargs['region']))
            all_subnets = self.get_all_subnets(**kwargs)

            if all_subnets:
                app.logger.debug("Found {} {}".format(len(all_subnets), self.i_am_plural))

                for subnet in all_subnets:

                    subnet_name = subnet.tags.get(u'Name', None)
                    if subnet_name:
                        subnet_name = "{0} ({1})".format(subnet_name, subnet.id)
                    else:
                        subnet_name = subnet.id

                    if self.check_ignore_list(subnet_name):
                        continue

                    arn = 'arn:aws:ec2:{region}:{account_number}:subnet/{subnet_id}'.format(
                        region=kwargs["region"],
                        account_number=kwargs["account_number"],
                        subnet_id=subnet.id)

                    config = {
                        "name": subnet.tags.get(u'Name', None),
                        "arn": arn,
                        "id": subnet.id,
                        "cidr_block": subnet.cidr_block,
                        "availability_zone": subnet.availability_zone,
                        # TODO:
                        # available_ip_address_count is likely to change often
                        # and should be in the upcoming ephemeral section.
                        # "available_ip_address_count": subnet.available_ip_address_count,
                        "defaultForAz": subnet.defaultForAz,
                        "mapPublicIpOnLaunch": subnet.mapPublicIpOnLaunch,
                        "state": subnet.state,
                        "tags": dict(subnet.tags),
                        "vpc_id": subnet.vpc_id
                    }

                    item = SubnetItem(region=kwargs['region'],
                                      account=kwargs['account_name'],
                                      name=subnet_name, config=config)

                    item_list.append(item)

            return item_list, exception_map
        return slurp_items()


class SubnetItem(ChangeItem):
    def __init__(self, region=None, account=None, name=None, arn=None, config={}):
        super(SubnetItem, self).__init__(
            index=Subnet.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config)
