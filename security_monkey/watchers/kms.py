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

from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey import app

from dateutil.tz import tzutc
import json

class KMS(Watcher):
    index = 'kms'
    i_am_singular = 'KMS Master Key'
    i_am_plural = 'KMS Master Keys'

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

    def list_keys(self, kms):
        all_keys = self.paged_wrap_aws_rate_limited_call(
            "Keys",
            kms.list_keys
        )
        return all_keys

    def list_aliases(self, kms):
        all_aliases = self.paged_wrap_aws_rate_limited_call(
            "Aliases",
            kms.list_aliases
        )
        return all_aliases

    def list_grants(self, kms, key_id):
        all_grants = self.paged_wrap_aws_rate_limited_call(
            "Grants",
            kms.list_grants,
            KeyId=key_id
        )
        return all_grants

    def describe_key(self, kms, key_id):
        response = self.wrap_aws_rate_limited_call(
            kms.describe_key,
            KeyId=key_id
        )
        return response.get("KeyMetadata")

    def list_key_policies(self, kms, key_id):
        policy_names = []
        try:
            policy_names = self.paged_wrap_aws_rate_limited_call(
                "PolicyNames",
                kms.list_key_policies,
                KeyId=key_id
            )
        except Exception as e:
            if e.response.get("Error").get("Code") == "AccessDeniedException":
                app.logger.debug("{} {} is an AWS supplied {} that has no policies".format(self.i_am_singular, key_id, self.i_am_singular))

        return policy_names

    def get_key_policy(self, kms, key_id, policy_name):
        policy = self.wrap_aws_rate_limited_call(
            kms.get_key_policy,
            KeyId=key_id,
            PolicyName=policy_name
        )
        return json.loads(policy.get("Policy"))

    def __init__(self, accounts=None, debug=False):
        super(KMS, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        """
        :returns: item_list - list of SES Identities.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()
        from security_monkey.common.sts_connect import connect
        item_list = []
        exception_map = {}
        for account in self.accounts:

            try:
                ec2 = connect(account, 'ec2')
                regions = ec2.get_all_regions()
            except Exception as e:  # EC2ResponseError
                # Some Accounts don't subscribe to EC2 and will throw an exception here.
                exc = BotoConnectionIssue(str(e), 'keypair', account, None)
                self.slurp_exception((self.index, account), exc, exception_map)
                continue

            for region in regions:
                keys = []
                aliases = []

                app.logger.debug("Checking {}/{}/{}".format(self.index, account, region.name))
                try:
                    kms = connect(account, 'boto3.kms.client', region=region.name)
                    # First, we'll get all the keys and aliases
                    keys = self.list_keys(kms)
                    # If we don't have any keys, don't bother getting aliases
                    if not(keys):
                        app.logger.debug("Found {} {}.".format(len(keys), self.i_am_plural))
                        continue
                    else:
                        aliases = self.list_aliases(kms)

                except Exception as e:
                    if region.name not in TROUBLE_REGIONS:
                        exc = BotoConnectionIssue(str(e), self.index, account, region.name)
                        self.slurp_exception((self.index, account, region.name), exc, exception_map)
                    continue

                app.logger.debug("Found {} {} and {} Aliases.".format(len(keys), self.i_am_plural, len(aliases)))
                # Then, we'll get info about each key
                for key in keys:
                    policies = []
                    key_id = key.get("KeyId")
                    # get the key's config object and grants
                    config = self.describe_key(kms, key_id)
                    grants = self.list_grants(kms, key_id)
                    policy_names = self.list_key_policies(kms, key_id)

                    for policy_name in policy_names:
                        policy = self.get_key_policy(kms, key_id, policy_name)
                        policies.append(policy)

                    # Convert the datetime objects into ISO formatted strings in UTC
                    if config.get('CreationDate'):
                        config.update({ 'CreationDate': config.get('CreationDate').astimezone(tzutc()).isoformat() })
                    if config.get('DeletionDate'):
                        config.update({ 'DeletionDate': config.get('DeletionDate').astimezone(tzutc()).isoformat() })

                    for grant in grants:
                        if grant.get("CreationDate"):
                            grant.update({ 'CreationDate': grant.get('CreationDate').astimezone(tzutc()).isoformat() })

                    config[u"Policies"] = policies
                    config[u"Grants"] = grants
                    # filter the list of all aliases and save them with the key they're for
                    config[u"Aliases"] = [a.get("AliasName") for a in aliases if a.get("TargetKeyId") == key_id]

                    item = KMSMasterKey(region=region.name, account=account, name=key_id, config=dict(config))
                    item_list.append(item)

        return item_list, exception_map


class KMSMasterKey(ChangeItem):
    def __init__(self, region=None, account=None, name=None, config={}):
        super(KMSMasterKey, self).__init__(
            index=KMS.index,
            region=region,
            account=account,
            name=name,
            new_config=config)
