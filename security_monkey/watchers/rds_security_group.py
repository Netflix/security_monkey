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
.. module: security_monkey.watchers.rds_security_group
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey.constants import IGNORE_PREFIX
from security_monkey import app
from boto.rds import regions


class RDSSecurityGroup(Watcher):
  index = 'rds'
  i_am_singular = 'RDS Security Group'
  i_am_plural = 'RDS Security Groups'

  def __init__(self, accounts=None, debug=False):
    super(RDSSecurityGroup, self).__init__(accounts=accounts, debug=debug)

  def slurp(self):
    """
    :returns: item_list - list of RDS Security Groups.
    :returns: exception_map - A dict where the keys are a tuple containing the
        location of the exception and the value is the actual exception

    """
    item_list = []
    exception_map = {}
    from security_monkey.common.sts_connect import connect
    for account in self.accounts:
      for region in regions():
        app.logger.debug("Checking {}/{}/{}".format(self.index, account, region.name))

        try:
          rds = connect(account, 'rds', region=region)
          sgs = self.wrap_aws_rate_limited_call(
            rds.get_all_dbsecurity_groups
          )
        except Exception as e:
          if region.name not in TROUBLE_REGIONS:
            exc = BotoConnectionIssue(str(e), self.index, account, region.name)
            self.slurp_exception((self.index, account, region.name), exc, exception_map)
          continue

        app.logger.debug("Found {} {}".format(len(sgs), self.i_am_plural))
        for sg in sgs:

          ### Check if this SG is on the Ignore List ###
          ignore_item = False
          for ignore_item_name in IGNORE_PREFIX[self.index]:
            if sg.name.lower().startswith(ignore_item_name.lower()):
              ignore_item = True
              break

          if ignore_item:
            continue

          item_config = {
            "name": sg.name,
            "description": sg.description,
            "owner_id": sg.owner_id,
            "region": region.name,
            "ec2_groups": [],
            "ip_ranges": []
          }

          for ipr in sg.ip_ranges:
            ipr_config = {
              "cidr_ip": ipr.cidr_ip,
              "status": ipr.status,
            }
            item_config["ip_ranges"].append(ipr_config)
          item_config["ip_ranges"] = sorted(item_config["ip_ranges"])

          for ec2_sg in sg.ec2_groups:
            ec2sg_config = {
              "name": ec2_sg.name,
              "owner_id": ec2_sg.owner_id,
              "Status": ec2_sg.Status,
            }
            item_config["ec2_groups"].append(ec2sg_config)
          item_config["ec2_groups"] = sorted(item_config["ec2_groups"])

          item = RDSSecurityGroupItem(region=region.name, account=account, name=sg.name, config=item_config)
          item_list.append(item)

    return item_list, exception_map


class RDSSecurityGroupItem(ChangeItem):
  def __init__(self, region=None, account=None, name=None, config={}):
    super(RDSSecurityGroupItem, self).__init__(
      index=RDSSecurityGroup.index,
      region=region,
      account=account,
      name=name,
      new_config=config)