#     Copyright 2018 Netflix, Inc.
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
.. module: security_monkey.watchers.vpc.vpc
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Mike Grima <mgrima@netflix.com>

"""
from boto3 import Session

from security_monkey.cloudaux_watcher import CloudAuxWatcher
from cloudaux.aws.ec2 import describe_vpcs
from cloudaux.orchestration.aws.vpc import get_vpc


class VPC(CloudAuxWatcher):
    index = 'vpc'
    i_am_singular = 'VPC'
    i_am_plural = 'VPCs'

    def __init__(self, *args, **kwargs):
        super(VPC, self).__init__(*args, **kwargs)
        self.honor_ephemerals = True
        self.ephemeral_paths = ['_version']
        self.service_name = 'vpc'

    def list_method(self, **kwargs):
        return describe_vpcs(**kwargs)

    def _get_regions(self):
        s = Session()
        return s.get_available_regions("ec2")

    def get_name_from_list_output(self, item):
        return item["VpcId"]

    def get_method(self, item, **kwargs):
        vpc = get_vpc(item["VpcId"], **kwargs)
        # Need to provide the friendly name:
        vpc["DEFERRED_ITEM_NAME"] = "{name} ({id})".format(name=vpc.get("Name"), id=vpc["Id"])

        return vpc
