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
from security_monkey.datastore import Account
from security_monkey import app, ARN_PREFIX


class SecurityGroup(Watcher):
    index = 'securitygroup'
    i_am_singular = 'Security Group'
    i_am_plural = 'Security Groups'

    def __init__(self, accounts=None, debug=False):
        super(SecurityGroup, self).__init__(accounts=accounts, debug=debug)
        # TODO: grab those from DB
        self.instance_detail = app.config.get("SECURITYGROUP_INSTANCE_DETAIL", 'FULL')
        self.honor_ephemerals = True
        self.ephemeral_paths = ["assigned_to"]

    def get_detail_level(self):
        """ Return details level: 'NONE' / 'SUMMARY' / 'FULL' """
        if self.instance_detail:
            return self.instance_detail

    def _build_rule(self, rule, rule_type):
        rule_list = []
        rule_config = {
            "ip_protocol": rule.get('IpProtocol'),
            "rule_type": rule_type,
            "from_port": rule.get('FromPort'),
            "to_port": rule.get('ToPort'),
            "cidr_ip": None,
            "owner_id": None,
            "group_id": None,
            "name": None
        }

        for ips in rule.get('IpRanges'):
            #make a copy of the base rule info.
            new_rule = rule_config.copy()
            new_rule['cidr_ip'] = ips.get('CidrIp')
            rule_list.append(new_rule)

        for ips in rule.get('Ipv6Ranges'):
            #make a copy of the base rule info.
            new_rule = rule_config.copy()
            new_rule['cidr_ip'] = ips.get('CidrIpv6')
            rule_list.append(new_rule)

        for user_id_group_pairs in rule.get('UserIdGroupPairs'):
            #make a copy of the base rule info.
            new_rule = rule_config.copy()
            new_rule['owner_id'] = user_id_group_pairs.get('UserId')
            new_rule['group_id'] = user_id_group_pairs.get('GroupId')
            new_rule['name'] = user_id_group_pairs.get('GroupName')
            rule_list.append(new_rule)

        return rule_list

    def slurp(self):
        """
        :returns: item_list - list of Security Groups.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()

        item_list = []
        exception_map = {}
        from security_monkey.common.sts_connect import connect
        for account in self.accounts:
            account_db = Account.query.filter(Account.name == account).first()
            account_number = account_db.identifier

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
                    # Retrieve security groups here
                    sgs = self.wrap_aws_rate_limited_call(
                        rec2.describe_security_groups
                    )

                    if self.get_detail_level() != 'NONE':
                        # We fetch tags here to later correlate instances
                        tags = self.wrap_aws_rate_limited_call(
                            rec2.describe_tags
                        )
                        # Retrieve all instances
                        instances = self.wrap_aws_rate_limited_call(
                            rec2.describe_instances
                        )
                        app.logger.info("Number of instances found in region {}: {}".format(region.name, len(instances)))
                except Exception as e:
                    if region.name not in TROUBLE_REGIONS:
                        exc = BotoConnectionIssue(str(e), self.index, account, region.name)
                        self.slurp_exception((self.index, account, region.name), exc, exception_map,
                                             source="{}-watcher".format(self.index))
                    continue

                app.logger.debug("Found {} {}".format(len(sgs), self.i_am_plural))

                if self.get_detail_level() != 'NONE':
                    app.logger.info("Creating mapping of sg_id's to instances")
                    # map sgid => instance
                    sg_instances = {}
                    for reservation in instances['Reservations']:
                        for instance in reservation['Instances']:
                            for group in instance['SecurityGroups']:
                                if group['GroupId'] not in sg_instances:
                                    sg_instances[group['GroupId']] = [instance]
                                else:
                                    sg_instances[group['GroupId']].append(instance)

                    app.logger.info("Creating mapping of instance_id's to tags")
                    # map instanceid => tags
                    instance_tags = {}
                    for tag in tags['Tags']:
                        if tag['ResourceId'] not in instance_tags:
                            instance_tags[tag['ResourceId']] = [tag]
                        else:
                            instance_tags[tag['ResourceId']].append(tag)
                    app.logger.info("Done creating mappings")

                for sg in sgs['SecurityGroups']:

                    if self.check_ignore_list(sg['GroupName']):
                        continue

                    arn = ARN_PREFIX + ':ec2:{region}:{account_number}:security-group/{security_group_id}'.format(
                        region=region.name,
                        account_number=account_number,
                        security_group_id=sg['GroupId'])

                    item_config = {
                        "id": sg['GroupId'],
                        "name": sg['GroupName'],
                        "description": sg.get('Description'),
                        "vpc_id": sg.get('VpcId'),
                        "owner_id": sg.get('OwnerId'),
                        "region": region.name,
                        "rules": [],
                        "assigned_to": None,
                        "arn": arn
                    }

                    for rule in sg['IpPermissions']:
                        item_config['rules'] += self._build_rule(rule, "ingress")

                    for rule in sg['IpPermissionsEgress']:
                        item_config['rules'] += self._build_rule(rule, "egress")

                    if self.get_detail_level() == 'SUMMARY':
                        if 'InstanceId' in sg and sg['InstanceId'] in sg_instances:
                            item_config["assigned_to"] = "{} instances".format(len(sg_instances[sg['GroupId']]))
                        else:
                            item_config["assigned_to"] = "0 instances"

                    elif self.get_detail_level() == 'FULL':
                        assigned_to = []
                        if sg['GroupId'] in sg_instances:
                            for instance in sg_instances[sg['GroupId']]:
                                if instance['InstanceId'] in instance_tags:
                                    tagdict = {tag['Key']: tag['Value'] for tag in instance_tags[instance['InstanceId']]}
                                    tagdict["instance_id"] = instance['InstanceId']
                                else:
                                    tagdict = {"instance_id": instance['InstanceId']}
                                assigned_to.append(tagdict)
                        item_config["assigned_to"] = assigned_to

                    # Issue 40: Security Groups can have a name collision between EC2 and
                    # VPC or between different VPCs within a given region.
                    if sg.get('VpcId'):
                        sg_name = "{0} ({1} in {2})".format(sg['GroupName'], sg['GroupId'], sg['VpcId'])
                    else:
                        sg_name = "{0} ({1})".format(sg['GroupName'], sg['GroupId'])

                    item = SecurityGroupItem(region=region.name, account=account, name=sg_name, arn=arn,
                                             config=item_config, source_watcher=self)
                    item_list.append(item)

        return item_list, exception_map


class SecurityGroupItem(ChangeItem):
    def __init__(self, region=None, account=None, name=None, arn=None, config=None, source_watcher=None):
        super(SecurityGroupItem, self).__init__(
            index=SecurityGroup.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config if config else {},
            source_watcher=source_watcher)
