#     Copyright 2018 Netflix, Inc.
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
.. module: security_monkey.tests.sso.header_auth
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Jordan Milne <jordan.milne@reddit.com>

"""

from mock import patch

from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.datastore import User


class HeaderAuthTestCase(SecurityMonkeyTestCase):
    def _get_user(self, email):
        return User.query.filter(User.email == email).scalar()

    def test_header_auth_disabled(self):
        with patch.dict(self.app.config, {"USE_HEADER_AUTH": False}):
            r = self.test_app.get('/login', headers={"Remote-User": "foo@example.com"})
            self.assertFalse(self._get_user("foo@example.com"))
            self.assertEqual(r.status_code, 200)

    def test_header_auth_enabled(self):
        with patch.dict(self.app.config, {"USE_HEADER_AUTH": True}):
            r = self.test_app.get('/login', headers={"Remote-User": "foo@example.com"})
            user = self._get_user("foo@example.com")
            self.assertIsNotNone(user)
            self.assertEqual(user.role, "View")
            self.assertEqual(r.status_code, 302)

    def test_header_auth_groups_used(self):
        with patch.dict(self.app.config, {"USE_HEADER_AUTH": True,
                                          "HEADER_AUTH_GROUPS_HEADER": "Remote-Groups",
                                          "ADMIN_GROUP": "admingroup",
                                          }):
            r = self.test_app.get('/login', headers={
                "Remote-User": "foo@example.com",
                "Remote-Groups": "foo,admingroup"
            })
            user = self._get_user("foo@example.com")
            self.assertIsNotNone(user)
            self.assertEqual(user.role, "Admin")
            self.assertEqual(r.status_code, 302)
