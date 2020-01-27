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
.. module: security_monkey.auditors.s3
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from six import text_type

from security_monkey.auditors.resource_policy_auditor import ResourcePolicyAuditor
from security_monkey.auditor import Entity
from security_monkey.watchers.s3 import S3
from security_monkey.datastore import Account


class S3Auditor(ResourcePolicyAuditor):
    index = S3.index
    i_am_singular = S3.i_am_singular
    i_am_plural = S3.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(S3Auditor, self).__init__(accounts=accounts, debug=debug)
        self.policy_keys = ['Policy']

    def prep_for_audit(self):
        super(S3Auditor, self).prep_for_audit()
        self.FRIENDLY_S3NAMES = [text_type(account['s3_name']).lower() for account in self.OBJECT_STORE['ACCOUNTS']['DESCRIPTIONS'] if account['label'] == 'friendly']
        self.THIRDPARTY_S3NAMES = [text_type(account['s3_name']).lower() for account in self.OBJECT_STORE['ACCOUNTS']['DESCRIPTIONS'] if account['label'] == 'thirdparty']
        self.FRIENDLY_S3CANONICAL = [text_type(account['s3_canonical_id']).lower() for account in self.OBJECT_STORE['ACCOUNTS']['DESCRIPTIONS'] if account['label'] == 'friendly']
        self.THIRDPARTY_S3CANONICAL = [text_type(account['s3_canonical_id']).lower() for account in self.OBJECT_STORE['ACCOUNTS']['DESCRIPTIONS'] if account['label'] == 'thirdparty']
        self.INTERNET_ACCESSIBLE = [
            'http://acs.amazonaws.com/groups/global/AuthenticatedUsers'.lower(),
            'http://acs.amazonaws.com/groups/global/AllUsers'.lower()]
        self.LOG_DELIVERY = ['http://acs.amazonaws.com/groups/s3/LogDelivery'.lower()]
        self.KNOWN_ACLS = self.FRIENDLY_S3NAMES + self.THIRDPARTY_S3NAMES + self.FRIENDLY_S3CANONICAL + self.THIRDPARTY_S3CANONICAL + self.INTERNET_ACCESSIBLE + self.LOG_DELIVERY

    def _check_acl(self, item, field, keys, recorder):
        acl = item.config.get('Grants', {})
        owner = item.config["Owner"]["ID"].lower()
        for key in list(acl.keys()):
            if key.lower() not in keys:
                continue

            # Canonical ID == Owning Account - No issue
            if key.lower() == owner.lower():
                continue

            entity = Entity(category='ACL', value=key)
            account = self._get_account(field, key)
            if account:
                entity.account_name=account['name']
                entity.account_identifier=account['identifier']
            recorder(item, actions=acl[key], entity=entity)

    def check_acl_internet_accessible(self, item):
        """ Handles AllUsers and AuthenticatedUsers. """
        self._check_acl(item, 'aws', self.INTERNET_ACCESSIBLE, self.record_internet_access)

    def check_acl_log_delivery(self, item):
        self._check_acl(item, 'aws', self.LOG_DELIVERY, self.record_thirdparty_access)

    def check_acl_friendly_legacy(self, item):
        self._check_acl(item, 's3_name', self.FRIENDLY_S3NAMES, self.record_friendly_access)

    def check_acl_thirdparty_legacy(self, item):
        self._check_acl(item, 's3_name', self.THIRDPARTY_S3NAMES, self.record_thirdparty_access)

    def check_acl_friendly_canonical(self, item):
        self._check_acl(item, 's3_canonical_id', self.FRIENDLY_S3CANONICAL, self.record_friendly_access)

    def check_acl_thirdparty_canonical(self, item):
        self._check_acl(item, 's3_canonical_id', self.THIRDPARTY_S3CANONICAL, self.record_thirdparty_access)

    def check_acl_unknown(self, item):
        acl = item.config.get('Grants', {})

        for key in list(acl.keys()):
            if key.lower() not in self.KNOWN_ACLS:
                entity = Entity(category='ACL', value=key)
                self.record_unknown_access(item, entity, actions=acl[key])

    def check_policy_exists(self, item):
        policy = item.config.get('Policy', {})
        if not policy:
            message = "POLICY - No Policy."
            self.add_issue(0, message, item)
