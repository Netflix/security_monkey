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
.. module: security_monkey.common.sts_connect
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.datastore import Account
import boto
import boto.ec2
import boto.iam
import boto.sns
import boto.sqs
import boto.rds


def connect(account_name, connection_type, **args):
    """

    Examples of use:
    ec2 = sts_connect.connect(environment, 'ec2', region=region, validate_certs=False)
    ec2 = sts_connect.connect(environment, 'ec2', validate_certs=False, debug=1000)
    ec2 = sts_connect.connect(environment, 'ec2')
    where environment is ( test, prod, dev )
    s3  = sts_connect.connect(environment, 's3')
    ses = sts_connect.connect(environment, 'ses')

    :param account: Account to connect with (i.e. test, prod, dev)

    :raises Exception: RDS Region not valid
                       AWS Tech not supported.

    :returns: STS Connection Object for given tech

    :note: To use this method a SecurityMonkey role must be created
            in the target account with full read only privledges.
    """
    account = Account.query.filter(Account.name == account_name).first()
    sts = boto.connect_sts()
    role = sts.assume_role('arn:aws:iam::' + account.number + ':role/SecurityMonkey', 'secmonkey')

    if connection_type == 'ec2':
        return boto.connect_ec2(
            role.credentials.access_key,
            role.credentials.secret_key,
            security_token=role.credentials.session_token,
            **args)

    if connection_type == 'elb':
        if 'region' in args:
            region = args['region']
            del args['region']
        else:
            region = 'us-east-1'

        return boto.ec2.elb.connect_to_region(
            region,
            aws_access_key_id=role.credentials.access_key,
            aws_secret_access_key=role.credentials.secret_key,
            security_token=role.credentials.session_token,
            **args)

    if connection_type == 's3':
        if 'region' in args:
            region = args['region']
            # drop region key-val pair from args or you'll get an exception
            del args['region']
            return boto.s3.connect_to_region(
                region,
                aws_access_key_id=role.credentials.access_key,
                aws_secret_access_key=role.credentials.secret_key,
                security_token=role.credentials.session_token,
                **args)

        return boto.connect_s3(
            role.credentials.access_key,
            role.credentials.secret_key,
            security_token=role.credentials.session_token,
            **args)

    if connection_type == 'ses':
        return boto.connect_ses(
            role.credentials.access_key,
            role.credentials.secret_key,
            security_token=role.credentials.session_token,
            **args)

    if connection_type == 'iam':
        if 'region' in args:
            region = args['region']
            # drop region key-val pair from args or you'll get an exception
            del args['region']
            return boto.iam.connect_to_region(
                region,
                aws_access_key_id=role.credentials.access_key,
                aws_secret_access_key=role.credentials.secret_key,
                security_token=role.credentials.session_token,
                **args)

        return boto.connect_iam(
            role.credentials.access_key,
            role.credentials.secret_key,
            security_token=role.credentials.session_token,
            **args)

    if connection_type == 'route53':
        return boto.connect_route53(
            role.credentials.access_key,
            role.credentials.secret_key,
            security_token=role.credentials.session_token,
            **args)

    if connection_type == 'sns':
        if 'region' in args:
            region = args['region']
            del args['region']
            return boto.sns.connect_to_region(
                region.name,
                aws_access_key_id=role.credentials.access_key,
                aws_secret_access_key=role.credentials.secret_key,
                security_token=role.credentials.session_token,
                **args)

        return boto.connect_sns(
            role.credentials.access_key,
            role.credentials.secret_key,
            security_token=role.credentials.session_token,
            **args)

    if connection_type == 'sqs':
        if 'region' in args:
            region = args['region']
            del args['region']
            return boto.sqs.connect_to_region(
                region.name,
                aws_access_key_id=role.credentials.access_key,
                aws_secret_access_key=role.credentials.secret_key,
                security_token=role.credentials.session_token,
                **args)

        return boto.connect_sqs(
            role.credentials.access_key,
            role.credentials.secret_key,
            security_token=role.credentials.session_token,
            **args)

    if connection_type == 'vpc':
        return boto.connect_vpc(
            role.credentials.access_key,
            role.credentials.secret_key,
            security_token=role.credentials.session_token,
            **args)

    if connection_type == 'rds':
        if 'region' in args:
            reg = args['region']
            rds_region = None
            for boto_region in boto.rds.regions():
                if reg.name == boto_region.name:
                    rds_region = boto_region

            if rds_region is None:
                raise Exception('The supplied region {0} is not in boto.rds.regions. {1}'.format(reg, boto.rds.regions()))

        return boto.connect_rds(
            role.credentials.access_key,
            role.credentials.secret_key,
            security_token=role.credentials.session_token,
            **args)

    err_msg = 'The connection_type supplied (%s) is not implemented.' % connection_type
    raise Exception(err_msg)
