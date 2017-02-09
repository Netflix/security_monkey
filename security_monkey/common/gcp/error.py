#     Copyright 2017 Google, Inc.
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
.. module: security_monkey.common.gcp.error
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Tom Melendez <supertom@google.com> @supertom

"""


class AuditIssue(object):

    def __init__(self, code, notes=None):
        self.code = code
        self.notes = notes
