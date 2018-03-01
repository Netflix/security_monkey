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
.. module: security_monkey.tests.utilities.test_user_utils
    :platform: Unix
.. version:: $$VERSION$$
.. moduleauthor::  Steve Kohrs <steve.kohrs@gmail.com>
"""
import mock
from mock import patch
from flask_security import SQLAlchemyUserDatastore
from flask_security.utils import encrypt_password
from flask.ext.script import prompt_pass
from security_monkey import db
from security_monkey.datastore import AccountType, User, Role
from security_monkey.manage import manager
from security_monkey.tests import SecurityMonkeyTestCase

class UserTestUtils(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        self.account_type = AccountType(name='AWS')
        db.session.add(self.account_type)
        db.session.commit()

    @patch('flask.ext.script.prompt_pass', return_value='r3s3tm3!')
    def test_create_user(self, prompt_pass_function):
        manager.handle("manage.py", ["create_user", "-e", "test@example.com", "--role", "View"])

        user = User.query.filter(User.email == email)
        assert user
        assert user.email == "test@example.com"
        assert user.role == "View"

        # Update existing user:
        manager.handle("manage.py", ["create_user", "-e", "test@example.com", "--role", "Comment"])

        user = User.query.filter(User.email == email)
        assert user
        assert user.role == "View"
