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
.. module: security_monkey.auditors.route53
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Alex Cline <alex.cline@gmail.com> @alex.cline

"""
from security_monkey.auditor import Auditor
from security_monkey.watchers.route53 import Route53
from security_monkey.common.utils import check_rfc_1918
import re


class Route53Auditor(Auditor):
    index = Route53.index
    i_am_singular = Route53.i_am_singular
    i_am_plural = Route53.i_am_plural
    internal_record_regex = [
        r"^internal-"
    ]

    def __init__(self, accounts=None, debug=False):
        super(Route53Auditor, self).__init__(accounts=accounts, debug=debug)

    def check_for_public_zone_with_private_records(self, route53_item):
        """
        alert when a public zone has private records.
        """
        if not route53_item.config.get('zoneprivate'):
            for r in route53_item.config.get('records'):
                for regex in self.internal_record_regex:
                    if re.match(regex, str(r)):
                        notes = ", ".join(route53_item.config.get('records'))
                        self.add_issue(1, 'Route53 public zone contains private record.', route53_item, notes=notes)
                try:
                    if check_rfc_1918(r):
                        notes = ", ".join(route53_item.config.get('records'))
                        self.add_issue(1, 'Route53 public zone contains private record.', route53_item, notes=notes)
                except:
                    # non IP's will throw an exception and that's okay.
                    pass

