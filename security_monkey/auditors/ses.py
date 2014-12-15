#     Copyright 2014 Yelp, Inc.
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
.. module: security_monkey.auditors.ses
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.auditor import Auditor
from security_monkey.watchers.ses import SES


class SESAuditor(Auditor):
    index = SES.index
    i_am_singular = SES.i_am_singular
    i_am_plural = SES.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(SESAuditor, self).__init__(accounts=accounts, debug=debug)


    def check_verified(self, ses_item):
        """
        alert when an SES identity is not verified.
        """
        if not ses_item.config.get('verified'):
            self.add_issue(1, 'SES Identity Not Verified.', ses_item)
