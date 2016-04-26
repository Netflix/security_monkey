#     Copyright 2015 Netflix, Inc.
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
.. module: security_monkey.auditors.elb
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Mike Grima <mgrima@netflix.com>

"""
from security_monkey.auditor import Auditor
from security_monkey.common.arn import ARN
from security_monkey.datastore import NetworkWhitelistEntry
from security_monkey.watchers.elasticsearch_service import ElasticSearchService

import ipaddr


class ElasticSearchServiceAuditor(Auditor):
    index = ElasticSearchService.index
    i_am_singular = ElasticSearchService.i_am_singular
    i_am_plural = ElasticSearchService.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(ElasticSearchServiceAuditor, self).__init__(accounts=accounts, debug=debug)

    def prep_for_audit(self):
        self.network_whitelist = NetworkWhitelistEntry.query.all()

    def _parse_arn(self, arn_input, account_numbers, es_domain):
        if arn_input == '*':
            notes = "An ElasticSearch Service domain policy where { 'Principal': { 'AWS': '*' } } must also have"
            notes += " a {'Condition': {'IpAddress': { 'AWS:SourceIp': '<ARN>' } } }"
            notes += " or it is open to any AWS account."
            self.add_issue(20, 'ES cluster open to all AWS accounts', es_domain, notes=notes)
            return

        arn = ARN(arn_input)
        if arn.error:
            self.add_issue(3, 'Auditor could not parse ARN', es_domain, notes=arn_input)
            return

        if arn.tech == 's3':
            notes = "The ElasticSearch Service domain allows access from S3 bucket [{}]. ".format(arn.name)
            notes += "Security Monkey does not yet have the capability to determine if this is "
            notes += "a friendly S3 bucket.  Please verify manually."
            self.add_issue(3, 'ES cluster allows access from S3 bucket', es_domain, notes=notes)
        else:
            account_numbers.append(arn.account_number)

    def check_es_access_policy(self, es_domain):
        policy = es_domain.config["policy"]

        for statement in policy.get("Statement", []):
            effect = statement.get("Effect")
            # We only care about "Allows"
            if effect.lower() == "deny":
                continue

            account_numbers = []
            princ = statement.get("Principal", {})
            if isinstance(princ, dict):
                princ_val = princ.get("AWS") or princ.get("Service")
            else:
                princ_val = princ

            if princ_val == "*":
                condition = statement.get('Condition', {})

                # Get the IpAddress subcondition:
                ip_addr_condition = condition.get("IpAddress")

                if ip_addr_condition:
                    source_ip_condition = ip_addr_condition.get("aws:SourceIp")

                if not ip_addr_condition or not source_ip_condition:
                    tag = "ElasticSearch Service domain open to everyone"
                    notes = "An ElasticSearch Service domain policy where { 'Principal': { '*' } } OR"
                    notes += " { 'Principal': { 'AWS': '*' } } must also have a"
                    notes += " {'Condition': {'IpAddress': { 'AWS:SourceIp': '<ARN>' } } }"
                    notes += " or it is open to the world. In this case, anyone is allowed to perform "
                    notes += " this action(s): {}".format(statement.get("Action"))
                    self.add_issue(20, tag, es_domain, notes=notes)

                else:
                    # Check for "aws:SourceIp" as a condition:
                    if isinstance(source_ip_condition, list):
                        for cidr in source_ip_condition:
                            self._check_proper_cidr(cidr, es_domain, statement.get("Action"))

                    else:
                        self._check_proper_cidr(source_ip_condition, es_domain, statement.get("Action"))

            else:
                if isinstance(princ_val, list):
                    for entry in princ_val:
                        arn = ARN(entry)
                        if arn.error:
                            self.add_issue(3, 'Auditor could not parse ARN', es_domain, notes=entry)
                            continue

                        if arn.root:
                            self._check_cross_account_root(es_domain, arn, statement.get("Action"))

                        if not arn.service:
                            account_numbers.append(arn.account_number)
                else:
                    arn = ARN(princ_val)
                    if arn.error:
                        self.add_issue(3, 'Auditor could not parse ARN', es_domain, notes=princ_val)
                    else:
                        if arn.root:
                            self._check_cross_account_root(es_domain, arn, statement.get("Action"))
                        if not arn.service:
                            account_numbers.append(arn.account_number)

            for account_number in account_numbers:
                self._check_cross_account(account_number, es_domain, 'policy')

    def _check_proper_cidr(self, cidr, es_domain, actions):
        try:
            any, ip_cidr = self._check_for_any_ip(cidr, es_domain, actions)
            if any:
                return

            if not self._check_inclusion_in_network_whitelist(cidr):
                message = "A CIDR that is not in the whitelist has access to this ElasticSearch Service domain:\n"
                message += "CIDR: {}, Actions: {}".format(cidr, actions)
                self.add_issue(5, message, es_domain, notes=cidr)

                # Check if the CIDR is in a large subnet (and not whitelisted):
                # Check if it's 10.0.0.0/8
                if ip_cidr == ipaddr.IPNetwork("10.0.0.0/8"):
                    message = "aws:SourceIp Condition contains a very large IP range: 10.0.0.0/8"
                    self.add_issue(7, message, es_domain, notes=cidr)
                else:
                    mask = int(ip_cidr.exploded.split('/')[1])
                    if 0 < mask < 24:
                        message = "aws:SourceIp contains a large IP Range: {}".format(cidr)
                        self.add_issue(3, message, es_domain, notes=cidr)


        except ValueError as ve:
            self.add_issue(3, 'Auditor could not parse CIDR', es_domain, notes=cidr)

    def _check_for_any_ip(self, cidr, es_domain, actions):
        if cidr == '*':
            self.add_issue(20, 'Any IP can perform the following actions against this ElasticSearch Service '
                               'domain:\n{}'.format(actions),
                           es_domain, notes=cidr)
            return True, None

        zero = ipaddr.IPNetwork("0.0.0.0/0")
        ip_cidr = ipaddr.IPNetwork(cidr)
        if zero == ip_cidr:
            self.add_issue(20, 'Any IP can perform the following actions against this ElasticSearch Service '
                               'domain:\n{}'.format(actions),
                           es_domain, notes=cidr)
            return True, None

        return False, ip_cidr

    def _check_inclusion_in_network_whitelist(self, cidr):
        for entry in self.network_whitelist:
            if ipaddr.IPNetwork(cidr) in ipaddr.IPNetwork(str(entry.cidr)):
                return True
        return False
