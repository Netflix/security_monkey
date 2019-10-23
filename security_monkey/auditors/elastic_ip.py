#     Copyright 2016 Netflix, Inc.
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
.. module: security_monkey.auditors.cloudtrail
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Nag Medida <nmedida@netflix.com>

"""
from security_monkey.auditor import Auditor, Categories
from security_monkey.watchers.elastic_ip import ElasticIP

from dumper import dump

class ElasticIPAuditor(Auditor):
    index = ElasticIP.index
    i_am_singular = ElasticIP.i_am_singular
    i_am_plural = ElasticIP.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(ElasticIPAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_if_eip_assigned(self, item):
        if item.config.get('network_interface_id', None) is None:
            self.add_issue(0, Categories.CANDIDATE_FOR_DELETION, item, notes="EIP is not associated with an ENI")
