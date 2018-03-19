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

        self.ephemeral_paths = [
            "instance_id",
            "network_interface_id",
            "network_interface_owner_id",
            "association_id",
            "private_ip_address"
        ]

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
                self.slurp_exception((self.index, account), exc, exception_map, source="{}-watcher".format(self.index))
                continue

            for region in regions:
                app.logger.debug("Checking {}/{}/{}".format(self.index, account, region.name))

                try:
                    rec2 = connect(account, 'boto3.ec2.client', region=region)
                    el_ips = self.wrap_aws_rate_limited_call(
                        rec2.describe_addresses
                    )
                    # Retrieve account tags to later match assigned EIP to instance
                    tags = self.wrap_aws_rate_limited_call(
                        rec2.describe_tags
                    )
                except Exception as e:
                    if region.name not in TROUBLE_REGIONS:
                        exc = BotoConnectionIssue(str(e), self.index, account, region.name)
                        self.slurp_exception((self.index, account, region.name), exc, exception_map,
                                             source="{}-watcher".format(self.index))
                    continue

                app.logger.debug("Found {} {}".format(len(el_ips), self.i_am_plural))
                for ip in el_ips['Addresses']:

                    if self.check_ignore_list(str(ip['PublicIp'])):
                        continue

                    instance_name = None
                    instance_tags = [x['Value'] for x in tags['Tags'] if x['Key'] == "Name" and
                                     x.get('ResourceId') == ip.get('InstanceId')]
                    if instance_tags:
                        (instance_name,) = instance_tags
                        if self.check_ignore_list(instance_name):
                            continue

                    item_config = {
                        "assigned_to": instance_name,
                        "public_ip": ip.get('PublicIp'),
                        "instance_id": ip.get('InstanceId'),
                        "domain": ip.get('Domain'),
                        "allocation_id": ip.get('AllocationId'),
                        "association_id": ip.get('AssociationId'),
                        "network_interface_id": ip.get('NetworkInterfaceId'),
                        "network_interface_owner_id": ip.get('NetworkInterfaceOwnerId'),
                        "private_ip_address": ip.get('PrivateIpAddress')
                    }

                    ip_label = "{0}".format(ip.get('PublicIp'))

                    item = ElasticIPItem(region=region.name, account=account, name=ip_label, config=item_config,
                                         source_watcher=self)
                    item_list.append(item)

        return item_list, exception_map


class ElasticIPItem(ChangeItem):
    def __init__(self, region=None, account=None, name=None, config=None, source_watcher=None):
        super(ElasticIPItem, self).__init__(
            index=ElasticIP.index,
            region=region,
            account=account,
            name=name,
            new_config=config if config else {},
            source_watcher=source_watcher)
