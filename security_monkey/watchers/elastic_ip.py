#     Copyright 2014 Rocket Internet AG (Luca Bruno)
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
.. module: security_monkey.watchers.elastic_ip
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Luca Bruno <luca.bruno@rocket-internet.de> @lucabruno

"""

from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey import app


class ElasticIP(Watcher):
    index = 'elasticip'
    i_am_singular = 'Elastic IP'
    i_am_plural = 'Elastic IPs'

    def __init__(self, accounts=None, debug=False):
        super(ElasticIP, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        """
        :returns: item_list - list of Elastic IPs.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()

        item_list = []
        exception_map = {}
        from security_monkey.common.sts_connect import connect
        for account in self.accounts:
            try:
                ec2 = connect(account, 'ec2')
                regions = ec2.get_all_regions()
            except Exception as e:  # EC2ResponseError
                # Some Accounts don't subscribe to EC2 and will throw an exception here.
                exc = BotoConnectionIssue(str(e), self.index, account, None)
                self.slurp_exception((self.index, account), exc, exception_map)
                continue

            for region in regions:
                app.logger.debug("Checking {}/{}/{}".format(self.index, account, region.name))

                try:
                    rec2 = connect(account, 'ec2', region=region)
                    el_ips = self.wrap_aws_rate_limited_call(
                        rec2.get_all_addresses
                    )
                    # Retrieve account tags to later match assigned EIP to instance
                    tags = self.wrap_aws_rate_limited_call(
                        rec2.get_all_tags
                    )
                except Exception as e:
                    if region.name not in TROUBLE_REGIONS:
                        exc = BotoConnectionIssue(str(e), self.index, account, region.name)
                        self.slurp_exception((self.index, account, region.name), exc, exception_map)
                    continue

                app.logger.debug("Found {} {}".format(len(el_ips), self.i_am_plural))
                for ip in el_ips:

                    if self.check_ignore_list(ip.instance_id):
                        continue

                    instance_name = None
                    instance_tags = [x.value for x in tags if x.name == "Name" and x.res_id == ip.instance_id]
                    if instance_tags:
                        (instance_name,) = instance_tags
                        if self.check_ignore_list(instance_name):
                            continue

                    item_config = {
                        "assigned_to": instance_name,
                        "public_ip": ip.public_ip,
                        "instance_id": ip.instance_id,
                        "domain": ip.domain,
                        "allocation_id": ip.allocation_id,
                        "association_id": ip.association_id,
                        "network_interface_id": ip.network_interface_id,
                        "network_interface_owner_id": ip.network_interface_owner_id,
                        "private_ip_address": ip.private_ip_address
                    }

                    ip_label = "{0}".format(ip.public_ip)

                    item = ElasticIPItem(region=region.name, account=account, name=ip_label, config=item_config)
                    item_list.append(item)

        return item_list, exception_map


class ElasticIPItem(ChangeItem):
    def __init__(self, region=None, account=None, name=None, config={}):
        super(ElasticIPItem, self).__init__(
            index=ElasticIP.index,
            region=region,
            account=account,
            name=name,
            new_config=config)
