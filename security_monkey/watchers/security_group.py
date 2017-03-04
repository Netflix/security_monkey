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

import copy

from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey.datastore import Account
from security_monkey import app


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
        else:
            return 'NONE'

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
                    rec2 = connect(account, 'ec2', region=region)
                    rds_region = copy.copy(region)
                    rds_region.endpoint = rds_region.endpoint.replace('ec2', 'rds')
                    rds = connect(account, 'rds', region=rds_region)
                    elb_conn = connect(account, 'elb', region=region.name)

                    # Retrieve security groups here
                    sgs = self.wrap_aws_rate_limited_call(
                        rec2.get_all_security_groups
                    )

                    if self.get_detail_level() != 'NONE':
                        # We fetch tags here to later correlate instances
                        tags = self.wrap_aws_rate_limited_call(
                            rec2.get_all_tags
                        )
                        # Retrieve all instances
                        instances = self.wrap_aws_rate_limited_call(
                            rec2.get_only_instances
                        )

                        # Retrieve RDS instances
                        rds_instances = self.wrap_aws_rate_limited_call(
                            rds.get_all_dbinstances
                        )
                        marker = None

                        # Retrieve ELBs
                        elbs = []
                        while True:
                            response = self.wrap_aws_rate_limited_call(
                                elb_conn.get_all_load_balancers,
                                marker=marker
                            )
                            elbs.extend(response)
                            if response.next_marker:
                                marker = response.next_marker
                            else:
                                break

                        # Retrieve redshift clusters
                        redshift = connect(account, 'redshift', region=region)
                        redshift_clusters = []
                        marker = None
                        while True:
                            response = self.wrap_aws_rate_limited_call(
                                redshift.describe_clusters,
                                marker=marker
                            )
                            redshift_clusters.extend(response['DescribeClustersResponse']['DescribeClustersResult']['Clusters'])
                            if response['DescribeClustersResponse']['DescribeClustersResult']['Marker'] is not None:
                                marker = response['DescribeClustersResponse']['DescribeClustersResult']['Marker']
                            else:
                                break

                        num_total_instances = len(instances) + len(rds_instances) + len(redshift_clusters) + len(elbs)
                        app.logger.info("Number of instances found in region {}: {} "
                                        "({} ec2, {} rds, {} redshift, {} elb)".format(region.name, num_total_instances, len(instances), 
                                                                                       len(rds_instances), len(redshift_clusters), len(elbs)))
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
                    sg_rds_instances = {}
                    sg_elb_instances = {}
                    sg_redshift_instances = {}
                    for instance in instances:
                        for group in instance.groups:
                            if group.id not in sg_instances:
                                sg_instances[group.id] = [instance]
                            else:
                                sg_instances[group.id].append(instance)

                    for rds_instance in rds_instances:
                        for group in rds_instance.vpc_security_groups:
                            if group.vpc_group not in sg_rds_instances:
                                sg_rds_instances[group.vpc_group] = [rds_instance.id]
                            else:
                                sg_rds_instances[group.vpc_group].append(rds_instance.id)

                    for elb in elbs:
                        for group in elb.security_groups:
                            elb_info = {'Load balancer': elb.name}
                            sg_elb_instances.setdefault(group, []).append(elb_info)

                    for redshift_cluster in redshift_clusters:
                        for sg in redshift_cluster['VpcSecurityGroups']:
                            if sg['Status'] == 'active':
                                cluster_info = {'Redshift ClusterIdentifier': redshift_cluster['ClusterIdentifier']}
                                sg_redshift_instances.setdefault(sg['VpcSecurityGroupId'], []).append(cluster_info)

                    app.logger.info("Creating mapping of instance_id's to tags")
                    # map instanceid => tags
                    instance_tags = {}
                    for tag in tags:
                        if tag.res_id not in instance_tags:
                            instance_tags[tag.res_id] = [tag]
                        else:
                            instance_tags[tag.res_id].append(tag)
                    app.logger.info("Done creating mappings")

                for sg in sgs:

                    if self.check_ignore_list(sg.name):
                        continue

                    arn = 'arn:aws:ec2:{region}:{account_number}:security-group/{security_group_id}'.format(
                        region=region.name,
                        account_number=account_number,
                        security_group_id=sg.id)

                    item_config = {
                        "id": sg.id,
                        "name": sg.name,
                        "description": sg.description,
                        "vpc_id": sg.vpc_id,
                        "owner_id": sg.owner_id,
                        "region": sg.region.name,
                        "rules": [],
                        "assigned_to": None,
                        "arn": arn
                    }

                    for rule in sg.rules:
                        for grant in rule.grants:
                            rule_config = {
                                "ip_protocol": rule.ip_protocol,
                                "rule_type": "ingress",
                                "from_port": rule.from_port,
                                "to_port": rule.to_port,
                                "cidr_ip": grant.cidr_ip,
                                "group_id": grant.group_id,
                                "name": grant.name,
                                "owner_id": grant.owner_id
                            }
                            item_config['rules'].append(rule_config)

                    for rule in sg.rules_egress:
                        for grant in rule.grants:
                            rule_config = {
                                "ip_protocol": rule.ip_protocol,
                                "rule_type": "egress",
                                "from_port": rule.from_port,
                                "to_port": rule.to_port,
                                "cidr_ip": grant.cidr_ip,
                                "group_id": grant.group_id,
                                "name": grant.name,
                                "owner_id": grant.owner_id
                            }
                            item_config['rules'].append(rule_config)
                    item_config['rules'] = sorted(item_config['rules'])

                    if self.get_detail_level() == 'SUMMARY':
                        num_inst = (len(sg_instances.get(sg.id, [])) + len(sg_rds_instances.get(sg.id, [])) + 
                                    len(sg_redshift_instances.get(sg.id, [])) + len(sg_elb_instances.get(sg.id, [])))
                        if sg.id in sg_instances:
                            item_config["assigned_to"] = "{} instances".format(num_inst)
                        else:
                            item_config["assigned_to"] = "0 instances"

                    elif self.get_detail_level() == 'FULL':
                        assigned_to = []
                        if sg.id in sg_instances:
                            for instance in sg_instances[sg.id]:
                                if instance.id in instance_tags:
                                    tagdict = {tag.name: tag.value for tag in instance_tags[instance.id]}
                                    tagdict["instance_id"] = instance.id
                                else:
                                    tagdict = {"instance_id": instance.id}
                                assigned_to.append(tagdict)
                        if sg.id in sg_rds_instances:
                            assigned_to.extend(sg_rds_instances[sg.id])
                        if sg.id in sg_elb_instances:
                            assigned_to.extend(sg_elb_instances[sg.id])
                        if sg.id in sg_redshift_instances:
                            assigned_to.extend(sg_redshift_instances[sg.id])
                        item_config["assigned_to"] = assigned_to

                    # Issue 40: Security Groups can have a name collision between EC2 and
                    # VPC or between different VPCs within a given region.
                    if sg.vpc_id:
                        sg_name = "{0} ({1} in {2})".format(sg.name, sg.id, sg.vpc_id)
                    else:
                        sg_name = "{0} ({1})".format(sg.name, sg.id)

                    item = SecurityGroupItem(region=region.name, account=account, name=sg_name, arn=arn, config=item_config)
                    item_list.append(item)

        return item_list, exception_map


class SecurityGroupItem(ChangeItem):
    def __init__(self, region=None, account=None, name=None, arn=None, config={}):
        super(SecurityGroupItem, self).__init__(
            index=SecurityGroup.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config)
