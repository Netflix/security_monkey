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
    error = False

    def __init__(self, input):
        arn_match = re.search('arn:aws:([^:]*):([^:]*):([^:]*):(.*)', input)
        if arn_match:
            return self._from_arn(arn_match, input)

        acct_number_match = re.search('^\d+$', input)
        if acct_number_match:
            return self._from_account_number(input)

        self.error = True
        app.logger.warn('ARN Could not parse [{}].'.format(input))

    def _from_arn(self, arn_match, input):
        self.tech = arn_match.group(1)
        self.region = arn_match.group(2)
        self.account_number = arn_match.group(3)
        self.name = arn_match.group(4)

    def _from_account_number(self, input):
        self.account_number = input
