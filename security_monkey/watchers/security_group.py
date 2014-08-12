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
.. module: security_monkey.watchers.security_group
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


class SecurityGroup(Watcher):
  index = 'securitygroup'
  i_am_singular = 'Security Group'
  i_am_plural = 'Security Groups'

  def __init__(self, accounts=None, debug=False):
    super(SecurityGroup, self).__init__(accounts=accounts, debug=debug)

  def slurp(self):
    """
    :returns: item_list - list of Security Groups.
    :returns: exception_map - A dict where the keys are a tuple containing the
        location of the exception and the value is the actual exception

    """
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
          sgs = self.wrap_aws_rate_limited_call(
            rec2.get_all_security_groups
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
            "id": sg.id,
            "name": sg.name,
            "description": sg.description,
            "vpc_id": sg.vpc_id,
            "owner_id": sg.owner_id,
            "region": sg.region.name,
            "rules": []
          }
          for rule in sg.rules:
            for grant in rule.grants:
              rule_config = {
                "ip_protocol": rule.ip_protocol,
                "from_port": rule.from_port,
                "to_port": rule.to_port,
                "cidr_ip": grant.cidr_ip,
                "group_id": grant.group_id,
                "name": grant.name,
                "owner_id": grant.owner_id
              }
              item_config['rules'].append(rule_config)
          item_config['rules'] = sorted(item_config['rules'])

          # Issue 40: Security Groups can have a name collision between EC2 and
          # VPC or between different VPCs within a given region.
          if sg.vpc_id:
              sg_name = "{0} ({1} in {2})".format(sg.name, sg.id, sg.vpc_id)
          else:
              sg_name = "{0} ({1})".format(sg.name, sg.id)

          item = SecurityGroupItem(region=region.name, account=account, name=sg_name, config=item_config)
          item_list.append(item)

    return item_list, exception_map


class SecurityGroupItem(ChangeItem):
  def __init__(self, region=None, account=None, name=None, config={}):
    super(SecurityGroupItem, self).__init__(
      index=SecurityGroup.index,
      region=region,
      account=account,
      name=name,
      new_config=config)
