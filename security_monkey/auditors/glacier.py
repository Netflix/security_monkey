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
.. module: security_monkey.auditors.glacier
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.watchers.glacier import GlacierVault
from security_monkey.auditors.resource_policy_auditor import ResourcePolicyAuditor


class GlacierVaultAuditor(ResourcePolicyAuditor):
    index = GlacierVault.index
    i_am_singular = GlacierVault.i_am_singular
    i_am_plural = GlacierVault.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(GlacierVaultAuditor, self).__init__(accounts=accounts, debug=debug)
        self.policy_keys = ['Policy']