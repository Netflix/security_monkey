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


class SecurityMonkeyTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.test_app = self.app.test_client()
        db.drop_all()
        db.create_all()
        self.pre_test_setup()

    def pre_test_setup(self):
        # Each sub-class can implement this.
        pass

    def tearDown(self):
        db.session.remove()
