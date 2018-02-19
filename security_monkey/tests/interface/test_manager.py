#     Copyright 2017 Bridgewater Associates
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
.. module: security_monkey.tests.interface.test_manager
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>

"""

from security_monkey.datastore import Account, Technology, Item, store_exception, ExceptionLogs, AccountType
from security_monkey import db, ARN_PREFIX
from security_monkey.tests import SecurityMonkeyTestCase

from security_monkey.manage import clear_expired_exceptions

import datetime


class ManageTestCase(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        account_type_result = AccountType.query.filter(AccountType.name == 'AWS').first()
        if not account_type_result:
            account_type_result = AccountType(name='AWS')
            db.session.add(account_type_result)
            db.session.commit()

        self.account = Account(identifier="012345678910", name="testing",
                               account_type_id=account_type_result.id)
        self.technology = Technology(name="iamrole")
        self.item = Item(region="us-west-2", name="testrole",
                         arn=ARN_PREFIX + ":iam::012345678910:role/testrole", technology=self.technology,
                         account=self.account)

        db.session.add(self.account)
        db.session.add(self.technology)
        db.session.add(self.item)

        db.session.commit()

    def test_clear_expired_exceptions(self):
        location = ("iamrole", "testing", "us-west-2", "testrole")

        for i in range(0, 5):
            try:
                raise ValueError("This is test: {}".format(i))
            except ValueError as e:
                test_exception = e

            store_exception("tests", location, test_exception,
                            ttl=(datetime.datetime.now() - datetime.timedelta(days=1)))

        store_exception("tests", location, test_exception)

        clear_expired_exceptions()

        # Get all the exceptions:
        exc_list = ExceptionLogs.query.all()

        assert len(exc_list) == 1
