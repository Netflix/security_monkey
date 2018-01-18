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
.. module: security_monkey.watchers.rds.rds_db_instance
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.decorators import record_exception, iter_account_region
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey import app


def process_db_instance(db_instance, **kwargs):
    app.logger.debug("Slurping {index} ({name}) from {account}".format(
        index=RDSDBInstance.i_am_singular,
        name=kwargs['name'],
        account=kwargs['account_name'])
    )

    return {
        'db_instance_identifier': kwargs['name'],
        'db_instance_class': db_instance.get('DBInstanceClass'),
        'engine': db_instance.get('Engine'),
        'db_instance_status': db_instance.get('DBInstanceStatus'),
        'master_username': db_instance.get('MasterUsername'),
        'db_name': db_instance.get('DBName'),
        'endpoint': db_instance.get('Endpoint'),
        'allocated_storage': db_instance.get('AllocatedStorage'),
        'instance_create_time': str(db_instance.get('InstanceCreateTime')),
        'preferred_backup_window': db_instance.get('PreferredBackupWindow'),
        'backup_retention_period': db_instance.get('BackupRetentionPeriod'),
        'db_security_groups': db_instance.get('DBSecurityGroups'),
        'vpc_security_groups': db_instance.get('VpcSecurityGroups'),
        'db_parameter_groups': db_instance.get('DBParameterGroups'),
        'availability_zone': db_instance.get('AvailabilityZone'),
        'db_subnet_group': db_instance.get('DBSubnetGroup'),
        'preferred_maintenance_window': db_instance.get('PreferredMaintenanceWindow'),
        'latest_restorable_time': str(db_instance.get('LatestRestorableTime')),
        'multi_az': db_instance.get('MultiAZ'),
        'engine_version': db_instance.get('EngineVersion'),
        'auto_minor_version_upgrade': db_instance.get('AutoMinorVersionUpgrade'),
        'read_replica_source_db_instance_identifier': db_instance.get('ReadReplicaSourceDBInstanceIdentifier'),
        'read_replica_db_instance_identifiers': db_instance.get('ReadReplicaDBInstanceIdentifiers'),
        'license_model': db_instance.get('LicenseModel'),
        'iops': db_instance.get('Iops'),
        'option_group_memberships': db_instance.get('OptionGroupMemberships'),
        'character_set_name': db_instance.get('CharacterSetName'),
        'secondary_availability_zone': db_instance.get('SecondaryAvailabilityZone'),
        'publicly_accessible': db_instance.get('PubliclyAccessible'),
        'storage_type': db_instance.get('StorageType'),
        'tde_credential_arn': db_instance.get('TdeCredentialArn'),
        'db_instance_port': db_instance.get('DbInstancePort'),
        'db_cluster_identifier': db_instance.get('DBClusterIdentifier'),
        'storage_encrypted': db_instance.get('StorageEncrypted'),
        'kms_key_id': db_instance.get('KmsKeyId'),
        'dbi_resource_id': db_instance.get('DbiResourceId'),
        'ca_certificate_identifier': db_instance.get('CACertificateIdentifier'),
        'copy_tags_to_snapshot': db_instance.get('CopyTagsToSnapshot'),
        'monitoring_interval': db_instance.get('MonitoringInterval'),
        'enhanced_monitoring_resource_arn': db_instance.get('EnhancedMonitoringResourceArn'),
        'monitoring_role_arn': db_instance.get('MonitoringRoleArn'),
        'arn': db_instance.get('DBInstanceArn')
    }


class RDSDBInstance(Watcher):
    index = 'rdsdbinstance'
    i_am_singular = 'RDS DB Instance'
    i_am_plural = 'RDS DB Instances'

    def __init__(self, accounts=None, debug=False):
        super(RDSDBInstance, self).__init__(accounts=accounts, debug=debug)
        self.honor_ephemerals = True
        self.ephemeral_paths = [
            "latest_restorable_time",
            "db_instance_status"
        ]

    @record_exception()
    def describe_db_instances(self, **kwargs):
        from security_monkey.common.sts_connect import connect
        rds = connect(kwargs['account_name'], 'boto3.rds.client', region=kwargs['region'],
                      assumed_role=kwargs['assumed_role'])

        response = self.wrap_aws_rate_limited_call(rds.describe_db_instances)
        rds_db_instances = response.get('DBInstances')
        return rds_db_instances

    def slurp(self):
        """
        :returns: item_list - list of RDS DB Instances.
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
            rds_db_instances = self.describe_db_instances(**kwargs)

            if rds_db_instances:
                app.logger.debug("Found {} {}".format(
                    len(rds_db_instances), self.i_am_plural))
                for db_instance in rds_db_instances:
                    name = db_instance.get('DBInstanceIdentifier')

                    if self.check_ignore_list(name):
                        continue

                    config = process_db_instance(
                        db_instance, name=name, account_name=kwargs['account_name'])

                    item = RDSDBInstanceItem(region=kwargs['region'],
                                             account=kwargs['account_name'],
                                             name=name, arn=config['arn'], config=dict(config),
                                             source_watcher=self)

                    item_list.append(item)

            return item_list, exception_map
        return slurp_items()


class RDSDBInstanceItem(ChangeItem):

    def __init__(self, region=None, account=None, name=None, arn=None, config=None, source_watcher=None):
        super(RDSDBInstanceItem, self).__init__(
            index=RDSDBInstance.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config if config else {},
            source_watcher=source_watcher)
