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
.. module: security_monkey.auditors.vpc.vpn
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Alex Cline <alex.cline@gmail.com> @alex.cline

"""
from security_monkey.auditor import Auditor
from security_monkey.watchers.vpc.vpn import VPN
import re


class VPNAuditor(Auditor):
    index = VPN.index
    i_am_singular = VPN.i_am_singular
    i_am_plural = VPN.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(VPNAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_tunnels(self, vpn_item):
        """
        alert when a VPN tunnel is not UP.
        """
        if vpn_item.config.get('tunnels'):
            for tunnel in vpn_item.config.get('tunnels'):
                if tunnel.get('status') != "UP":
                    notes = "{} - {} - {}".format(tunnel.get('outside_ip_address'), tunnel.get('status'), tunnel.get('status_message'))
                    self.add_issue(1, "{} tunnel is not UP".format(self.i_am_singular), vpn_item, notes=notes)

