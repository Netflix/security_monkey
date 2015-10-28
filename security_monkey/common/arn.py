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
.. module: security_monkey.common.arn
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com>

"""

import re
from security_monkey import app


class ARN(object):
    tech = None
    region = None
    account_number = None
    name = None
    partition = None
    error = False

    def __init__(self, input):
        arn_match = re.search('^arn:([^:]*):([^:]*):([^:]*):(|[\d]{12}):(.+)$', input)
        if arn_match:
            return self._from_arn(arn_match, input)

        acct_number_match = re.search('^(\d{12})+$', input)
        if acct_number_match:
            return self._from_account_number(input)

        self.error = True
        app.logger.warn('ARN Could not parse [{}].'.format(input))

    def _from_arn(self, arn_match, input):
        self.partition = arn_match.group(1)
        self.tech = arn_match.group(2)
        self.region = arn_match.group(3)
        self.account_number = arn_match.group(4)
        self.name = arn_match.group(5)

    def _from_account_number(self, input):
        self.account_number = input

    @staticmethod
    def extract_arns_from_statement_condition(condition):
        condition_subsection \
            = condition.get('ArnEquals', {}) or \
              condition.get('ForAllValues:ArnEquals', {}) or \
              condition.get('ForAnyValue:ArnEquals', {}) or \
              condition.get('ArnLike', {}) or \
              condition.get('ForAllValues:ArnLike', {}) or \
              condition.get('ForAnyValue:ArnLike', {}) or \
              condition.get('StringLike', {}) or \
              condition.get('ForAllValues:StringLike', {}) or \
              condition.get('ForAnyValue:StringLike', {}) or \
              condition.get('StringEquals', {}) or \
              condition.get('ForAllValues:StringEquals', {}) or \
              condition.get('ForAnyValue:StringEquals', {})

        # aws:sourcearn can be found with in lowercase or camelcase or other cases...
        condition_arns = []
        for key, value in condition_subsection.iteritems():
            if key.lower() == 'aws:sourcearn' or key.lower() == 'aws:sourceowner':
                condition_arns.append(value)

        if not isinstance(condition_arns, list):
            return [condition_arns]
        return condition_arns
