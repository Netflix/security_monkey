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
.. module: security_monkey.auditors.sns
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.watchers.sns import SNS
from security_monkey.auditor import Categories, Entity
from security_monkey.auditors.resource_policy_auditor import ResourcePolicyAuditor
from policyuniverse.arn import ARN


class SNSAuditor(ResourcePolicyAuditor):
    index = SNS.index
    i_am_singular = SNS.i_am_singular
    i_am_plural = SNS.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(SNSAuditor, self).__init__(accounts=accounts, debug=debug)
        self.policy_keys = ['policy']

    def check_snstopicpolicy_empty(self, snsitem):
        """
        alert on empty SNS Policy
        """
        tag = "SNS Topic Policy is empty"
        severity = 1
        if snsitem.config.get('policy', {}) == {}:
            self.add_issue(severity, tag, snsitem, notes=None)

    def check_subscriptions_crossaccount(self, item):
        """
        "subscriptions": [
          {
               "Owner": "020202020202",
               "Endpoint": "someemail@example.com",
               "Protocol": "email",
               "TopicArn": ARN_PREFIX + ":sns:" + AWS_DEFAULT_REGION + ":020202020202:somesnstopic",
               "SubscriptionArn": ARN_PREFIX + ":sns:" + AWS_DEFAULT_REGION + ":020202020202:somesnstopic:..."
          }
        ]
        """
        subscriptions = item.config.get('subscriptions', [])
        for subscription in subscriptions:
            src_account_number = subscription.get('Owner', None)

            entity = Entity(
                category=subscription.get('Protocol'),
                value=subscription.get('Endpoint'),
                account_identifier=src_account_number,
                account_name='UNKNOWN')

            account = self._get_account('identifier', src_account_number)
            if not account:
                self.record_unknown_access(item, entity, actions=['subscription'])
                continue

            if account['name'] == item.account:
                # Same Account
                continue

            entity.account_name = account['name']
            if account['label'] == 'friendly':
                self.record_friendly_access(item, entity, actions=['subscription'])
            elif account['label'] == 'thirdparty':
                self.record_thirdparty_access(item, entity, actions=['subscription'])
