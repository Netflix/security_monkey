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
.. module: security_monkey.auditors.elb
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.watchers.elb import ELB
from security_monkey.auditor import Auditor


class ELBAuditor(Auditor):
    index = ELB.index
    i_am_singular = ELB.i_am_singular
    i_am_plural = ELB.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(ELBAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_internet_scheme(self, elb_item):
        """
        alert when an ELB has an "internet-facing" scheme.
        """
        scheme = elb_item.config.get('scheme', None)
        if scheme and scheme == u"internet-facing":
            self.add_issue(1, 'ELB is Internet accessible.', elb_item)

