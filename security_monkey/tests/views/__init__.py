#     Copyright 2016 Bridgewater Associates
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
.. module: security_monkey.tests.watchers.test_lambda_function
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>
"""

from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey import db
from flask_security import SQLAlchemyUserDatastore
from security_monkey.datastore import User
from security_monkey.datastore import Role
from datetime import datetime
from flask_security.utils import encrypt_password


class SecurityMonkeyApiTestCase(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        self.app_context = self.app.app_context()
        self.app_context.push()
        test_user_email = 'test@test.com'
        test_user_password = 'test'
        self.create_test_user(test_user_email, test_user_password)
        self.login(test_user_email, test_user_password)

    def create_test_user(self, email, password):
        user_datastore = SQLAlchemyUserDatastore(db, User, Role)
        user = user_datastore.create_user(email=email, password=encrypt_password(password), confirmed_at=datetime.now())
        user.role = 'Admin'
        user.active = True

        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)

    def login(self, email=None, password=None):
        email = email or self.user.email
        password = password or 'password'
        response = self.test_app.post(
            '/login',
            data={'email': email, 'password': password},
            follow_redirects=False
        )
        self.headers = {
            'cookie': response.headers[3][1],
            'Content-Type': 'application/json'
        }

        return response
