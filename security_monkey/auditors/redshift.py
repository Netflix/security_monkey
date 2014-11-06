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
.. module: security_monkey.auditors.redshift
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Ivan Leichtling <ivanlei@yelp.com> @c0wl

"""
from security_monkey.auditor import Auditor
from security_monkey.watchers.redshift import Redshift


class RedshiftAuditor(Auditor):
    index = Redshift.index
    i_am_singular = Redshift.i_am_singular
    i_am_plural = Redshift.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(RedshiftAuditor, self).__init__(accounts=accounts, debug=debug)

    def prep_for_audit(self):
        """
        Prepare for the audit by calculating 90 days ago.
        This is used to check if access keys have been rotated.
        """
        pass

    def check_running_in_vpc(self, redshift_cluster):
        """
        alert when not running in a VPC.
        """
        if not redshift_cluster.config.get('VpcId'):
            message = "POLICY - Redshift cluster not in VPC."
            self.add_issue(10, message, redshift_cluster)
        