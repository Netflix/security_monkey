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
.. module: security_monkey.tests.core.test_sso_service
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.sso.service import setup_user
from security_monkey.datastore import User
from security_monkey import db


class SSOServiceTestCase(SecurityMonkeyTestCase):
    def test_create_user(self):
        existing_user = User(
            email='test@test.com',
            active=True,
            role='View'
        )
        db.session.add(existing_user)
        db.session.commit()
        db.session.refresh(existing_user)

        user1 = setup_user('test@test.com')
        self.assertEqual(existing_user.id, user1.id)
        self.assertEqual(existing_user.role, user1.role)

        user2 = setup_user('test2@test.com')
        self.assertEqual(user2.email, 'test2@test.com')
        self.assertEqual(user2.role, 'View')

        self.app.config.update(
            ADMIN_GROUP='test_admin_group',
            JUSTIFY_GROUP='test_justify_group',
            VIEW_GROUP='test_view_group'
        )
        admin_user = setup_user('admin@test.com', ['test_admin_group'])
        justify_user = setup_user('justifier@test.com', ['test_justify_group'])
        view_user = setup_user('viewer@test.com', ['test_view_group'])

        self.assertEqual(admin_user.role, 'Admin')
        self.assertEqual(justify_user.role, 'Justify')
        self.assertEqual(view_user.role, 'View')
