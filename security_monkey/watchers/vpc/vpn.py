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
.. module: security_monkey.watchers.vpc.vpn
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Alex Cline <alex.cline@gmail.com> @alex.cline

"""
from cloudaux.aws.ec2 import describe_vpn_connections

from security_monkey.cloudaux_watcher import CloudAuxWatcher
from security_monkey.watcher import ChangeItem

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


class VPN(CloudAuxWatcher):
    index = 'vpn'
    i_am_singular = 'VPN Connection'
    i_am_plural = 'VPN Connections'

    def __init__(self, *args, **kwargs):
        super(VPN, self).__init__(*args, **kwargs)
        self.honor_ephemerals = True
        self.ephemeral_paths = [
            'VgwTelemetry$*$LastStatusChange',
            'VgwTelemetry$*$Status',
            'VgwTelemetry$*$StatusMessage',
        ]

    def get_name_from_list_output(self, item):
        if item.get("Tags"):
            for tag in item["Tags"]:
                if tag["Key"] == "Name":
                    return "{} ({})".format(tag["Value"], item["VpnConnectionId"])

        return item["VpnConnectionId"]

    def list_method(self, **kwargs):
        return describe_vpn_connections(**kwargs)

    def get_method(self, item, **kwargs):
        # Remove the CustomerGatewayConfiguration -- it's not necessary as all the details are present anyway:
        item.pop("CustomerGatewayConfiguration", None)

        # Set the ARN:
        item["Arn"] = "arn:aws:ec2:{region}:{account}:vpn-connection/{id}".format(region=kwargs["region"],
                                                                                  account=kwargs["account_number"],
                                                                                  id=item["VpnConnectionId"])

        # Cast the datetimes to something JSON serializable (ISO 8601 string):
        for vgw in item.get("VgwTelemetry", []):
            if vgw.get("LastStatusChange"):
                vgw["LastStatusChange"] = vgw["LastStatusChange"].strftime(DATETIME_FORMAT)

        return item


class VPNItem(ChangeItem):
    def __init__(self, region=None, account=None, name=None, arn=None, config=None, source_watcher=None):
        super(VPNItem, self).__init__(
            index=VPN.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config if config else {},
            source_watcher=source_watcher)
