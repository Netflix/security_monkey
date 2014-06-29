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
.. module: security_monkey.tests.__init__
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com>

"""

import unittest
from security_monkey import app, db


class SecurityMonkey(object):
  def setUp(self):
    self.test_app = app.test_client()
    db.create_all()

  def tearDown(self):
    db.session.remove()
    # db.drop_all()


class SecurityMonkeyTestCase(SecurityMonkey, unittest.TestCase):
  pass
