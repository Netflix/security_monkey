#     Copyright 2017 Netflix, Inc.
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
.. module: security_monkey.auditors.lambda_function
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <patrick@netflix.com>

"""

from security_monkey.auditors.resource_policy_auditor import ResourcePolicyAuditor
from security_monkey.watchers.lambda_function import LambdaFunction

from policyuniverse.arn import ARN
import json


class LambdaFunctionAuditor(ResourcePolicyAuditor):
    index = LambdaFunction.index
    i_am_singular = LambdaFunction.i_am_singular
    i_am_plural = LambdaFunction.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(LambdaFunctionAuditor, self).__init__(accounts=accounts, debug=debug)
        self.policy_keys = ['Policy$DEFAULT', 'Policy$Aliases', 'Policy$Versions']
