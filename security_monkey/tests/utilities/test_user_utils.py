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
import pytest
from mock import patch
from security_monkey import db
from security_monkey.datastore import AccountType, User
from security_monkey.manage import manager
from security_monkey.tests import SecurityMonkeyTestCase


class UserTestUtils(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        self.account_type = AccountType(name='AWS')
        db.session.add(self.account_type)
        db.session.commit()

    @patch('security_monkey.manage.prompt_pass', return_value='r3s3tm3!')
    def test_create_user(self, prompt_pass_function):
        email = "test@example.com"
        manager.handle("manage.py", ["create_user", email, "View"])

        user = User.query.filter(User.email == email).one()
        assert user
        assert user.email == "test@example.com"
        assert user.role == "View"

        # Update existing user:
        manager.handle("manage.py", ["create_user", email, "Comment"])
        user = User.query.filter(User.email == email).one()
        assert user
        assert user.role == "Comment"

    def test_toggle_active_user(self):
        test_user = User(email='test@example.com')
        test_user.role = 'View'
        test_user.active = False
        db.session.add(test_user)
        db.session.commit()

        manager.handle('manage.py', ['toggle_active_user', '--email', 'test@example.com', '--active', 'True'])
        assert User.query.filter(User.email == 'test@example.com').first().active

        manager.handle('manage.py', ['toggle_active_user', '--email', 'test@example.com'])
        assert not User.query.filter(User.email == 'test@example.com').first().active

        with pytest.raises(SystemExit):
            manager.handle('manage.py', ['toggle_active_user', '--email', 'notauser'])


    # Commented out because user deletion is broken.
    # def test_delete_user(self):
    #     test_user = User(email='test@example.com')
    #     test_user.role = 'View'
    #     db.session.add(test_user)
    #     db.session.commit()
    #
    #     manager.handle('manage.py', ['delete_user', 'test@example.com'])
    #     assert not User.query.filter(User.email == 'test@example.com').first()
    #
    #     with pytest.raises(SystemExit):
    #         manager.handle('manage.py', ['delete_user', 'test@example.com'])
