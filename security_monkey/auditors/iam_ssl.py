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
.. module: security_monkey.auditors.iam_ssl
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from dateutil.tz import tzutc
from dateutil import parser

from security_monkey.watchers.iam.iam_ssl import IAMSSL
from security_monkey.auditor import Auditor


# April 1, 2014
HEARTBLEED_DATE = '2014-04-01T00:00:00Z'

class IAMSSLAuditor(Auditor):
    index = IAMSSL.index
    i_am_singular = IAMSSL.i_am_singular
    i_am_plural = IAMSSL.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(IAMSSLAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_cert_size_lt_1024(self, cert_item):
        """
        alert when a cert is using less than 1024 bits
        """
        size = cert_item.config.get('size', None)
        if size and size < 1024:
            notes = 'Actual size is {0} bits.'.format(size)
            self.add_issue(10, 'Cert size is less than 1024 bits.', cert_item, notes=notes)

    def check_cert_size_lt_2048(self, cert_item):
        """
        alert when a cert is using less than 2048 bits
        """
        size = cert_item.config.get('size', None)
        if size and 1024 <= size < 2048:
            notes = 'Actual size is {0} bits.'.format(size)
            self.add_issue(3, 'Cert size is less than 2048 bits.', cert_item, notes=notes)

    def check_signature_algorith_for_md5(self, cert_item):
        """
        alert when a cert is using md5 for the hashing part
         of the signature algorithm
        """
        sig_alg = cert_item.config.get('signature_algorithm', None)
        if sig_alg and 'md5' in sig_alg.lower():
            self.add_issue(3, 'Cert uses an MD5 signature Algorithm', cert_item, notes=sig_alg)

    def check_signature_algorith_for_sha1(self, cert_item):
        """
        alert when a cert is using sha1 for the hashing part of
         its signature algorithm.
        Microsoft and Google are aiming to drop support for sha1 by January 2017.
        """
        sig_alg = cert_item.config.get('signature_algorithm', None)
        if sig_alg and 'sha1' in sig_alg.lower():
            self.add_issue(1, 'Cert uses an SHA1 signature Algorithm', cert_item, notes=sig_alg)

    def check_upcoming_expiration(self, cert_item):
        """
        alert when a cert's expiration is within 30 days
        """
        expiration = cert_item.config.get('expiration', None)
        if expiration:
            expiration = parser.parse(expiration)
            now = expiration.now(tzutc())
            time_to_expiration = (expiration - now).days
            if 0 <= time_to_expiration <= 30:
                notes = 'Expires on {0}.'.format(str(expiration))
                self.add_issue(10, 'Cert will expire soon.', cert_item, notes=notes)

    def check_expired(self, cert_item):
        """
        alert when a cert's expiration is within 30 days
        """
        expiration = cert_item.config.get('expiration', None)
        if expiration:
            expiration = parser.parse(expiration)
            now = expiration.now(tzutc())
            time_to_expiration = (expiration - now).days
            if time_to_expiration < 0:
                notes = 'Expired on {0}.'.format(str(expiration))
                self.add_issue(10, 'Cert has expired.', cert_item, notes=notes)

    def check_upload_date_for_heartbleed(self, cert_item):
        """
        alert when a cert was uploaded pre-heartbleed.
        """
        upload = cert_item.config.get('upload_date', None)
        if upload:
            upload = parser.parse(upload)
            heartbleed = parser.parse(HEARTBLEED_DATE)
            if upload < heartbleed:
                notes = "Cert was uploaded {0} days before heartbleed.".format((heartbleed-upload).days)
                self.add_issue(10, 'Cert may have been compromised by heartbleed.', cert_item, notes=notes)
