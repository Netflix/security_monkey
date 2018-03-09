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
.. module: security_monkey.watchers.eni
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey import app


class ENI(Watcher):
    index = 'networkinterface'
    i_am_singular = 'ENI'
    i_am_plural = 'ENIs'

    def __init__(self, accounts=None, debug=False):
        super(ENI, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        """
        :returns: item_list - list of networkinterface items.
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
                app.logger.debug(
                    "Checking {}/{}/{}".format(self.index, account, 'universal'))
                el_nis = self.wrap_aws_rate_limited_call(
                    ec2.get_all_network_interfaces
                )
            except Exception as e:  # EC2ResponseError
                # Some Accounts don't subscribe to EC2 and will throw an
                # exception here.
                exc = BotoConnectionIssue(str(e), self.index, account, None)
                self.slurp_exception(
                    (self.index, account, 'universal'), exc, exception_map)
                continue

            app.logger.debug("Found {} {}.".format(
                len(el_nis), self.i_am_plural))

            for network_interface in el_nis:

                if self.check_ignore_list(network_interface.id):
                    continue

                item_config = {
                    'availability_zone': network_interface.availability_zone,
                    'description': network_interface.description,
                    'network_interface_id': network_interface.id,
                    'mac_address': network_interface.mac_address,
                    'owner_id': network_interface.owner_id,
                    'private_ip_address': network_interface.private_ip_address,
                    'source_dest_check': network_interface.source_dest_check,
                    'status': network_interface.status,
                    'vpc_id': network_interface.vpc_id
                }

                if hasattr(network_interface, 'allocationId'):
                    item_config[
                        'allocation_id'] = network_interface.allocationId
                if hasattr(network_interface, 'associationId'):
                    item_config[
                        'association_id'] = network_interface.associationId
                if hasattr(network_interface, 'attachment') and (network_interface.attachment is not None):
                    attachment = network_interface.attachment
                    item_config['attachment'] = {
                        'attach_time': str(attachment.attach_time),
                        'delete_on_termination': attachment.delete_on_termination,
                        'device_index': attachment.device_index,
                        'id': attachment.id,
                        'instance_id': attachment.instance_id,
                        'instance_owner_id': attachment.instance_owner_id,
                        'status': attachment.status
                    }
                if hasattr(network_interface, 'privateDnsName'):
                    item_config[
                        'private_dns_name'] = network_interface.privateDnsName
                if hasattr(network_interface, 'publicDnsName'):
                    item_config[
                        'public_dns_name'] = network_interface.publicDnsName
                if hasattr(network_interface, 'publicIp'):
                    item_config[
                        'public_ip_address'] = network_interface.publicIp
                if hasattr(network_interface, 'ipOwnerId'):
                    item_config['ip_owner_id'] = network_interface.ipOwnerId

                item = ENIItem(region='universal', account=account,
                               name=network_interface.id, config=item_config, source_watcher=self)
                item_list.append(item)

        return item_list, exception_map


class ENIItem(ChangeItem):

    def __init__(self, account=None, region=None, name=None, config=None, source_watcher=None):
        super(ENIItem, self).__init__(
            index=ENI.index,
            region=region,
            account=account,
            name=name,
            new_config=config if config else {},
            source_watcher=source_watcher)
