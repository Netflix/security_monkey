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
.. module: security_monkey.watchers.iam.iam_role
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey.exceptions import AWSRateLimitReached
from boto.exception import BotoServerError
from security_monkey import app
from joblib import Parallel, delayed

import json
import urllib


# def all_managed_policies(conn):
#     managed_policies = {}
#
#     for policy in conn.policies.all():
#         for attached_role in policy.attached_roles.all():
#             policy_dict = {
#                 "name": policy.policy_name,
#                 "arn": policy.arn,
#                 "version": policy.default_version_id
#             }
#
#             if attached_role.arn not in managed_policies:
#                 managed_policies[attached_role.arn] = [policy_dict]
#             else:
#                 managed_policies[attached_role.arn].append(policy_dict)
#
#     return managed_policies


from functools import wraps
from itertools import product
from security_monkey.datastore import Account
from security_monkey.decorators import sts_conn, rate_limited


###--- DECORATORS ---###


def record_exception():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                index = kwargs.get('index')
                account = kwargs.get('account')
                region = kwargs.get('region')
                exception_map = kwargs.get('exception_map')
                exc = BotoConnectionIssue(str(e), 'iamrole', account, None)
                exception_map[(index, account, region)] = exc
        return decorated_function
    return decorator


def iter_account_region(accounts=None, regions=None):
    regions = regions or ['us-east-1']

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            item_list = []; exception_map = {}
            for account_name, region in product(accounts, regions):
                account = Account.query.filter(Account.name == account_name).first()
                if not account:
                    print "Couldn't find account with name",account_name
                    return
                kwargs['account_name'] = account.name
                kwargs['account_number'] = account.number
                kwargs['assume_role'] = account.role_name or 'SecurityMonkey'
                itm, exc = f(*args, **kwargs)
                item_list.extend(itm)
                exception_map.update(exc)
            return item_list, exception_map
        return decorated_function
    return decorator



###--- BOTO CALLS ---###


@sts_conn('iam', service_type='client')
@rate_limited()
def _get_role_managed_policies(role, client=None, **kwargs):
    marker = {}
    policies = []

    while True:
        response = client.list_attached_role_policies(
            RoleName=role['RoleName'],
            **marker
        )
        policies.extend(response['AttachedPolicies'])

        if response['IsTruncated']:
            marker['Marker'] = response['Marker']
        else:
            break

    return [{'name': p['PolicyName'], 'arn': p['PolicyArn']} for p in policies]


@sts_conn('iam', service_type='client')
@rate_limited()
def _get_role_instance_profiles(role, client=None, **kwargs):
    marker = {}
    instance_profiles = []

    while True:
        response = client.list_instance_profiles_for_role(
            RoleName=role['RoleName'],
            **marker
        )
        instance_profiles.extend(response['InstanceProfiles'])

        if response['IsTruncated']:
            marker['Marker'] = response['Marker']
        else:
            break

    return [
        {
            'path': ip['Path'],
            'instance_profile_name': ip['InstanceProfileName'],
            'create_date': ip['CreateDate'].strftime('%Y-%m-%dT%H:%M:%SZ'),
            'instance_profile_id': ip['InstanceProfileId'],
            'arn': ip['Arn']
        } for ip in instance_profiles
    ]




@sts_conn('iam', service_type='client')
@rate_limited()
def _get_role_inline_policy_document(role, policy_name, client=None, **kwargs):
    response = client.get_role_policy(
        RoleName=role['RoleName'],
        PolicyName=policy_name
    )
    return response.get('PolicyDocument')


###--- iam_role logic ---###


def _basic_config(role):
    return {
        'role': {
            'path': role.get('Path'),
            'role_name': role.get('RoleName'),
            'create_date': role.get('CreateDate').strftime('%Y-%m-%dT%H:%M:%SZ'),
            'arn': role.get('Arn'),
            'role_id': role.get('RoleId')
        },
        'assume_role_policy_document': role.get('AssumeRolePolicyDocument')
    }


def _get_role_inline_policies(role, **kwargs):
    policy_names = _get_role_inline_policy_names(role, **kwargs)

    policies = zip(
        policy_names,
        Parallel(n_jobs=20, backend="threading")(
            delayed(_get_role_inline_policy_document)
            (role, policy_name, **kwargs) for policy_name in policy_names
        )
    )
    policies = dict(policies)

    # for policy_name in policy_names:
    #     policies[policy_name] = _get_role_inline_policy_document(role, policy_name, **kwargs)

    return policies

# @rate_limited()
@sts_conn('iam', service_type='client')
def _get_role_inline_policy_names(role, client=None, **kwargs):
    marker = {}
    inline_policies = []

    while True:
        response = client.list_role_policies(
            RoleName=role['RoleName'],
            **marker
        )
        inline_policies.extend(response['PolicyNames'])

        if response['IsTruncated']:
            marker['Marker'] = response['Marker']
        else:
            return inline_policies


 # @record_exception()
def process_role(role, **kwargs):
    print "processing role",role['RoleName']
    config = _basic_config(role)

    config.update(
        {
            # 'managed_policies': _get_role_managed_policies(role, **kwargs),
            'rolepolicies': _get_role_inline_policies(role, **kwargs),
            'instance_profiles': _get_role_instance_profiles(role, **kwargs)
        }
    )

    return config

class IAMRole(Watcher):
    index = 'iamrole'
    i_am_singular = 'IAM Role'
    i_am_plural = 'IAM Roles'

    def __init__(self, accounts=None, debug=False):
        super(IAMRole, self).__init__(accounts=accounts, debug=debug)

    # @record_exception()
    @sts_conn('iam')
    def list_roles(self, **kwargs):
        client = kwargs['client']
        roles = []
        marker = {}

        while True:
            response = client.list_roles(**marker)
            roles.extend(response['Roles'])

            if response['IsTruncated']:
                marker['Marker'] = response['Marker']
            else:
                return roles



    def slurp(self):
        self.prep_for_slurp()
        print ""
        print "STARTING"
        print ""

        @iter_account_region(accounts=self.accounts, regions=['us-east-1'])
        def slurp_items(*args, **kwargs):
            item_list = []
            exception_map = {}

            exc_args = {
                'index': self.index,
                'account': kwargs['account_name'],
                'region': 'universal',
                'exception_map': exception_map,

                'account_number': kwargs['account_number'],
                'assume_role': kwargs['assume_role']
            }

            roles = self.list_roles(**exc_args)
            roles = [role for role in roles if not self.check_ignore_list(role['RoleName'])]

            # policies = zip(
            #     policy_names,
            #     Parallel(n_jobs=20, backend="threading")(
            #         delayed(_get_role_inline_policy_document)
            #         (role, policy_name, **kwargs) for policy_name in policy_names
            #     )
            # )
            # policies = dict(policies)

            # backend="threading"
            roles = zip(
                [role['RoleName'] for role in roles],
                Parallel(n_jobs=100)(
                    delayed(process_role)
                    (role, **exc_args) for role in roles
                )
            )
            for role in roles:
                item = IAMRoleItem(account=kwargs['account_name'], name=role[0], config=role[1])
                item_list.append(item)

            # for role in roles:
            #     config = self.process_role(role, **exc_args)
            #     item = IAMRoleItem(account=kwargs['account_name'], name=role['RoleName'], config=config)
            #     item_list.append(item)

            return item_list, exception_map
        return slurp_items()


class IAMRoleItem(ChangeItem):
    def __init__(self, account=None, name=None, config={}):
        super(IAMRoleItem, self).__init__(
            index=IAMRole.index,
            region='universal',
            account=account,
            name=name,
            new_config=config)
