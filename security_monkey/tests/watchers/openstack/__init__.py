#     Copyright (c) 2017 AT&T Intellectual Property. All rights reserved.
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
.. module: security_monkey.tests.watchers.openstack
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Michael Stair <mstair@att.com>

"""
from security_monkey.tests.watchers import SecurityMonkeyWatcherTestCase
from security_monkey.datastore import Account, AccountType
from security_monkey import db

import mock

from cloudaux.tests.openstack.mock_decorators import mock_openstack_conn, mock_get_regions, mock_iter_account_region
from cloudaux.tests.openstack.mock_utils import mock_list_items
from cloudaux.openstack.decorators import openstack_conn, get_regions, iter_account_region
from cloudaux.openstack.utils import list_items

""" Patch all of the CloudAux decorators. Must do this before importing watchers """

mock.patch('cloudaux.openstack.decorators.openstack_conn', mock_openstack_conn).start()
mock.patch('cloudaux.openstack.decorators.iter_account_region', mock_iter_account_region).start()
mock.patch('cloudaux.openstack.decorators.get_regions', mock_get_regions).start()
mock.patch('cloudaux.openstack.utils.list_items', mock_list_items).start()


class OpenStackWatcherTestCase(SecurityMonkeyWatcherTestCase):

    def pre_test_setup(self):
        account_type_result = AccountType(name='OpenStack')
        db.session.add(account_type_result)
        db.session.commit()

        self.account = Account(identifier="012345678910", name="TEST_ACCOUNT",
                               account_type_id=account_type_result.id, notes="TEST_ACCOUNT",
                               third_party=False, active=True)

        db.session.add(self.account)
        db.session.commit()

        self.watcher = None

    def test_slurp(self):
        if not self.watcher: return

        item_list, exception_map = self.watcher.slurp()

        self.assertIs(
            expr1=len(item_list),
            expr2=1,
            msg="Watcher should have 1 item but has {}".format(len(item_list)))
