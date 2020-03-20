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
.. module: security_monkey.watchers.kms
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Alex Cline <alex.cline@gmail.com> @alex.cline

"""
from security_monkey.decorators import record_exception
from security_monkey.decorators import iter_account_region
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey import app, ARN_PREFIX

from dateutil.tz import tzutc
import json
from botocore.exceptions import ClientError


class KMS(Watcher):
    index = 'kms'
    i_am_singular = 'KMS Master Key'
    i_am_plural = 'KMS Master Keys'

    @record_exception()
    def connect_to_kms(self, **kwargs):
        from security_monkey.common.sts_connect import connect
        return connect(kwargs['account_name'], 'boto3.kms.client', region=kwargs['region'],
                       assumed_role=kwargs['assumed_role'])

    def paged_wrap_aws_rate_limited_call(self, type, func, *args, **nargs):
        marker = None
        all_results = []
        while True:
            if marker is None:
                response = self.wrap_aws_rate_limited_call(func, *args, **nargs)
            else:
                nargs["Marker"] = marker
                response = self.wrap_aws_rate_limited_call(func, *args, **nargs)
            all_results.extend(response.get(type))
            marker = response.get("NextMarker")
            if marker is None:
                break
        return all_results

    @record_exception()
    def list_keys(self, kms, **kwargs):
        all_keys = self.paged_wrap_aws_rate_limited_call(
            "Keys",
            kms.list_keys
        )
        return all_keys

    @record_exception()
    def list_aliases(self, kms, **kwargs):
        all_aliases = self.paged_wrap_aws_rate_limited_call(
            "Aliases",
            kms.list_aliases
        )
        return all_aliases

    @record_exception()
    def list_grants(self, kms, key_id, **kwargs):
        all_grants = self.paged_wrap_aws_rate_limited_call(
            "Grants",
            kms.list_grants,
            KeyId=key_id
        )
        return all_grants

    @record_exception()
    def describe_key(self, kms, key_id, **kwargs):
        try:
            response = self.wrap_aws_rate_limited_call(
                kms.describe_key,
                KeyId=key_id
            )
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") != "AccessDeniedException":
                raise

            arn = ARN_PREFIX + ":kms:{}:{}:key/{}".format(kwargs['region'],
                                                    kwargs['account_name'],
                                                    key_id)

            return {
                       'Error': 'Unauthorized',
                       'Arn': arn,
                       "AWSAccountId": kwargs['account_name'],
                       'Policies': [],
                       'Grants': []
                   }

        return response.get("KeyMetadata")

    @record_exception()
    def list_key_policies(self, kms, key_id, alias, **kwargs):
        policy_names = []
        if alias.startswith('alias/aws/'):
            # AWS-owned KMS keys don't have a policy we can see. Setting a default here saves an API request.
            app.logger.debug("{} {}({}) is an AWS supplied KMS key, overriding to [default] for policy".format(self.i_am_singular, alias, key_id))
            policy_names = ['default']
        else:
            try:
                policy_names = self.paged_wrap_aws_rate_limited_call(
                        "PolicyNames",
                        kms.list_key_policies,
                        KeyId=key_id
                    )
            except ClientError as e:
                raise

        return policy_names

    @record_exception()
    def get_key_policy(self, kms, key_id, policy_name, alias, **kwargs):
        policy = self.wrap_aws_rate_limited_call(
            kms.get_key_policy,
            KeyId=key_id,
            PolicyName=policy_name
        )

        return json.loads(policy.get("Policy"))

    @record_exception()
    def get_key_rotation_status(self, kms, key_id, alias, **kwargs):
        rotation_status = None
        if alias.startswith('alias/aws/'):
            # AWS-owned KMS keys don't have a rotation status we can see. Setting a default here saves an API request.
            app.logger.debug("{} {}({}) is an AWS supplied KMS key, overriding to True for rotation state".format(self.i_am_singular, alias, key_id))
            rotation_status = True
        else:
            rotation_status = self.wrap_aws_rate_limited_call(
                kms.get_key_rotation_status,
                KeyId=key_id
            ).get("KeyRotationEnabled")

        return rotation_status

    def __init__(self, accounts=None, debug=False):
        super(KMS, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        """
        :returns: item_list - list of KMS keys.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()

        @iter_account_region(index=self.index, accounts=self.accounts, service_name='kms')
        def slurp_items(**kwargs):
            item_list = []
            exception_map = {}
            kwargs['exception_map'] = exception_map

            app.logger.debug("Checking {}/{}/{}".format(self.index,
                                                        kwargs['account_name'],
                                                        kwargs['region']))

            kms = self.connect_to_kms(**kwargs)

            if kms:
                # First, we'll get all the keys and aliases
                keys = self.list_keys(kms, **kwargs)
                # If we don't have any keys, don't bother getting aliases
                if keys:
                    app.logger.debug("Found {} {}.".format(len(keys), self.i_am_plural))
                    aliases = self.list_aliases(kms, **kwargs)

                    app.logger.debug("Found {} {} and {} Aliases.".format(len(keys), self.i_am_plural, len(aliases)))
                    # Then, we'll get info about each key
                    for key in keys:
                        policies = []
                        key_id = key.get("KeyId")
                        # get the key's config object and grants
                        config = self.describe_key(kms, key_id, **kwargs)
                        if config:
                            # filter the list of all aliases and save them with the key they're for
                            config["Aliases"] = [a.get("AliasName") for a in aliases if a.get("TargetKeyId") == key_id]

                            if config["Aliases"]:
                                alias = config["Aliases"][0]
                                alias = alias[len('alias/'):]  # Turn alias/name into just name
                            else:
                                alias = "[No Aliases]"

                            name = "{alias} ({key_id})".format(alias=alias, key_id=key_id)

                            if config.get('Error') is None:
                                grants = self.list_grants(kms, key_id, **kwargs)
                                policy_names = self.list_key_policies(kms, key_id, alias, **kwargs)
                                rotation_status = self.get_key_rotation_status(kms, key_id, alias, **kwargs)

                                if policy_names:
                                    for policy_name in policy_names:
                                        policy = self.get_key_policy(kms, key_id, policy_name, alias, **kwargs)
                                        policies.append(policy)

                                # Convert the datetime objects into ISO formatted strings in UTC
                                if config.get('CreationDate'):
                                    config.update({ 'CreationDate': config.get('CreationDate').astimezone(tzutc()).isoformat() })
                                if config.get('DeletionDate'):
                                    config.update({ 'DeletionDate': config.get('DeletionDate').astimezone(tzutc()).isoformat() })

                                if grants:
                                    for grant in grants:
                                        if grant.get("CreationDate"):
                                            grant.update({ 'CreationDate': grant.get('CreationDate').astimezone(tzutc()).isoformat() })

                                config["Policies"] = policies
                                config["Grants"] = grants
                                config["KeyRotationEnabled"] = rotation_status

                            item = KMSMasterKey(region=kwargs['region'], account=kwargs['account_name'], name=name,
                                                arn=config.get('Arn'), config=dict(config), source_watcher=self)
                            item_list.append(item)

            return item_list, exception_map
        return slurp_items()


class KMSMasterKey(ChangeItem):
    def __init__(self, region=None, account=None, name=None, arn=None, config=None, source_watcher=None):
        super(KMSMasterKey, self).__init__(
            index=KMS.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config if config else {},
            source_watcher=source_watcher)
