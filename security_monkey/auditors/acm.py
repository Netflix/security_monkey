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
.. module: security_monkey.watchers.acm
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Alex Cline <alex.cline@gmail.com> @alex.cline

"""
from security_monkey.auditor import Auditor
from security_monkey.watchers.acm import ACM
from dateutil.tz import tzutc
from dateutil import parser


class ACMAuditor(Auditor):
    index = ACM.index
    i_am_singular = ACM.i_am_singular
    i_am_plural = ACM.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(ACMAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_upcoming_expiration(self, cert_item):
        """
        alert when a cert's expiration is within 30 days
        """
        expiration = cert_item.config.get('NotAfter', None)
        if expiration:
            expiration = parser.parse(expiration)
            now = expiration.now(tzutc())
            time_to_expiration = (expiration - now).days
            if 0 <= time_to_expiration <= 30:
                notes = 'Expires on {0}.'.format(str(expiration))
                self.add_issue(10, 'Cert will expire soon.', cert_item, notes=notes)

    def check_future_expiration(self, cert_item):
        """
        alert when a cert's expiration is within 60 days
        """
        expiration = cert_item.config.get('NotAfter', None)
        if expiration:
            expiration = parser.parse(expiration)
            now = expiration.now(tzutc())
            time_to_expiration = (expiration - now).days
            if 0 <= time_to_expiration <= 60:
                notes = 'Expires on {0}.'.format(str(expiration))
                self.add_issue(5, 'Cert will expire soon.', cert_item, notes=notes)

    def check_expired(self, cert_item):
        """
        alert when a cert is expired
        """
        expiration = cert_item.config.get('NotAfter', None)
        if expiration:
            expiration = parser.parse(expiration)
            now = expiration.now(tzutc())
            time_to_expiration = (expiration - now).days
            if time_to_expiration < 0:
                notes = 'Expired on {0}.'.format(str(expiration))
                self.add_issue(10, 'Cert has expired.', cert_item, notes=notes)