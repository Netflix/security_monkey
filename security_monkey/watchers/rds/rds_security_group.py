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
.. module: security_monkey.watchers.rds.rds_security_group
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>

"""
from security_monkey.decorators import record_exception, iter_account_region
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey import app


class RDSSecurityGroup(Watcher):
    index = 'rdssecuritygroup'
    i_am_singular = 'RDS Security Group'
    i_am_plural = 'RDS Security Groups'

    def __init__(self, accounts=None, debug=False):
        super(RDSSecurityGroup, self).__init__(accounts=accounts, debug=debug)

    @record_exception()
    def get_all_dbsecurity_groups(self, **kwargs):
        from security_monkey.common.sts_connect import connect
        sgs = []
        rds = connect(kwargs['account_name'], 'boto3.rds.client', region=kwargs['region'],
                      assumed_role=kwargs['assumed_role'])

        marker = None
        while True:
            if marker:
                response = self.wrap_aws_rate_limited_call(
                    rds.describe_db_security_groups, Marker=marker)
            else:
                response = self.wrap_aws_rate_limited_call(
                    rds.describe_db_security_groups)

            sgs.extend(response.get('DBSecurityGroups', []))
            if response.get('Marker'):
                marker = response.get('Marker')
            else:
                break
        return sgs

    def slurp(self):
        """
        :returns: item_list - list of RDS Security Groups.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()

        @iter_account_region(index=self.index, accounts=self.accounts, service_name='rds')
        def slurp_items(**kwargs):
            item_list = []
            exception_map = {}
            kwargs['exception_map'] = exception_map
            app.logger.debug("Checking {}/{}/{}".format(self.index,
                                                        kwargs['account_name'], kwargs['region']))
            sgs = self.get_all_dbsecurity_groups(**kwargs)

            if sgs:
                app.logger.debug("Found {} {}".format(
                    len(sgs), self.i_am_plural))
                for sg in sgs:
                    name = sg.get('DBSecurityGroupName')
                    if self.check_ignore_list(name):
                        continue

                    vpc_id = None
                    if hasattr(sg, 'VpcId'):
                        vpc_id = sg.get('VpcId')
                        name = "{} (in {})".format(name, vpc_id)

                    item_config = {
                        "name": name,
                        "description": sg.get('DBSecurityGroupDescription'),
                        "owner_id": sg.get('OwnerId'),
                        "region": kwargs['region'],
                        "ec2_groups": [],
                        "ip_ranges": [],
                        "vpc_id": vpc_id
                    }

                    for ipr in sg.get('IPRanges'):
                        ipr_config = {
                            "cidr_ip": ipr.get('CIDRIP'),
                            "status": ipr.get('Status'),
                        }
                        item_config["ip_ranges"].append(ipr_config)

                    for ec2_sg in sg.get('EC2SecurityGroups'):
                        ec2sg_config = {
                            "name": ec2_sg.get('EC2SecurityGroupName'),
                            "owner_id": ec2_sg.get('EC2SecurityGroupOwnerId'),
                            "Status": ec2_sg.get('Status'),
                        }
                        item_config["ec2_groups"].append(ec2sg_config)

                    arn = sg.get('DBSecurityGroupArn')

                    item_config['arn'] = arn

                    item = RDSSecurityGroupItem(region=kwargs['region'],
                                                account=kwargs['account_name'],
                                                name=name, arn=arn, config=item_config, source_watcher=self)

                    item_list.append(item)

            return item_list, exception_map
        return slurp_items()


class RDSSecurityGroupItem(ChangeItem):

    def __init__(self, region=None, account=None, name=None, arn=None, config=None, source_watcher=None):
        super(RDSSecurityGroupItem, self).__init__(
            index=RDSSecurityGroup.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config if config else {},
            source_watcher=source_watcher)
