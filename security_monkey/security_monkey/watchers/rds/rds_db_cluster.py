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
.. module: security_monkey.watchers.rds.rds_db_cluster
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey import app
from boto.rds import regions


class RDSDBCluster(Watcher):
    index = 'rdsdbcluster'
    i_am_singular = 'RDS DB Cluster'
    i_am_plural = 'RDS DB Clusters'

    def __init__(self, accounts=None, debug=False):
        super(RDSDBCluster, self).__init__(accounts=accounts, debug=debug)
        self.honor_ephemerals = True
        self.ephemeral_paths = [
            "latest_restorable_time",
            "earliest_restorable_time",
        ]

    def slurp(self):
        """
        :returns: item_list - list of RDS DB Clusters.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()

        item_list = []
        exception_map = {}
        from security_monkey.common.sts_connect import connect
        for account in self.accounts:
            for region in regions():
                app.logger.debug(
                    "Checking {}/{}/{}".format(self.index, account, region.name))

                clusters = []
                try:
                    rds = connect(account, 'boto3.rds.client', region=region)

                    marker = None
                    while True:
                        if marker:
                            response = self.wrap_aws_rate_limited_call(
                                rds.describe_db_clusters,
                                Marker=marker
                            )

                        else:
                            response = self.wrap_aws_rate_limited_call(
                                rds.describe_db_clusters
                            )

                        clusters.extend(response.get('DBClusters', []))
                        if response.get('Marker'):
                            marker = response.get('Marker')
                        else:
                            break

                except Exception as e:
                    if region.name not in TROUBLE_REGIONS:
                        exc = BotoConnectionIssue(
                            str(e), self.index, account, region.name)
                        self.slurp_exception(
                            (self.index, account, region.name), exc, exception_map)
                    continue

                app.logger.debug("Found {} {}".format(
                    len(clusters), self.i_am_plural))
                for cluster in clusters:

                    name = cluster.get('DBClusterIdentifier')

                    if self.check_ignore_list(name):
                        continue

                    item_config = {
                        'name': name,
                        'allocated_storage': cluster.get('AllocatedStorage'),
                        'availability_zones': cluster.get('AvailabilityZones'),
                        'backup_retention_period': cluster.get('BackupRetentionPeriod'),
                        'character_set_name': cluster.get('CharacterSetName'),
                        'database_name': cluster.get('DatabaseName'),
                        'db_cluster_parameter_group': cluster.get('DBClusterParameterGroup'),
                        'db_subnet_group': cluster.get('DBSubnetGroup'),
                        'status': cluster.get('Status'),
                        'percent_progress': cluster.get('PercentProgress'),
                        'earliest_restorable_time': str(cluster.get('EarliestRestorableTime')),
                        'endpoint': cluster.get('Endpoint'),
                        'engine': cluster.get('Engine'),
                        'engine_version': cluster.get('EngineVersion'),
                        'latest_restorable_time': str(cluster.get('LatestRestorableTime')),
                        'port': cluster.get('Port'),
                        'master_username': cluster.get('MasterUsername'),
                        'db_cluster_option_group_memberships': cluster.get('DBClusterOptionGroupMemberships', []),
                        'preferred_backup_window': cluster.get('PreferredBackupWindow'),
                        'preferred_maintenance_window': cluster.get('PreferredMaintenanceWindow'),
                        'db_cluster_members': cluster.get('DBClusterMembers', []),
                        'vpc_security_groups': cluster.get('VpcSecurityGroups', []),
                        'hosted_zoneId': cluster.get('HostedZoneId'),
                        'storage_encrypted': cluster.get('StorageEncrypted', False),
                        'kms_key_id': cluster.get('KmsKeyId'),
                        'db_cluster_resourceId': cluster.get('DbClusterResourceId'),
                        'arn': cluster.get('DBClusterArn')
                    }

                    item = RDSClusterItem(
                        region=region.name, account=account, name=name, arn=cluster.get('DBClusterArn'),
                        config=item_config, source_watcher=self)
                    item_list.append(item)

        return item_list, exception_map


class RDSClusterItem(ChangeItem):

    def __init__(self, region=None, account=None, name=None, arn=None, config=None, source_watcher=None):
        super(RDSClusterItem, self).__init__(
            index=RDSDBCluster.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config if config else {},
            source_watcher=source_watcher)
