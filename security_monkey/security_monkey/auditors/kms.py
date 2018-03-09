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
.. module: security_monkey.auditors.kms
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Alex Cline <alex.cline@gmail.com> @alex.cline
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.watchers.kms import KMS
from security_monkey.auditors.resource_policy_auditor import ResourcePolicyAuditor
import json


class KMSAuditor(ResourcePolicyAuditor):
    index = KMS.index
    i_am_singular = KMS.i_am_singular
    i_am_plural = KMS.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(KMSAuditor, self).__init__(accounts=accounts, debug=debug)
        self.policy_keys = ['Policies']

    def check_for_kms_key_rotation(self, kms_item):
        """
        Alert when a KMS key is not configured for rotation
        This is a AWS CIS Foundations Benchmark audit item (2.8)
        """
        rotation_status = kms_item.config.get('KeyRotationEnabled')
        if not rotation_status:
            self.add_issue(1, 'KMS key is not configured for rotation.', kms_item)
