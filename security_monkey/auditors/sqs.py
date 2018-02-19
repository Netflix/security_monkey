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
.. module: security_monkey.auditors.sqs
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Denver Janke <denverjanke@gmail.com>

"""

from security_monkey.auditors.resource_policy_auditor import ResourcePolicyAuditor
from security_monkey.watchers.sqs import SQS


class SQSAuditor(ResourcePolicyAuditor):
    index = SQS.index
    i_am_singular = SQS.i_am_singular
    i_am_plural = SQS.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(SQSAuditor, self).__init__(accounts=accounts, debug=debug)
        self.policy_keys = ['Policy']
