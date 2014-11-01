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

from flask.ext.login import current_user, logout_user
from flask.ext.restful import Resource


# End the Flask-Logins session
class Logout(Resource):
    def __init__(self):
        super(Logout, self).__init__()

    def get(self):
        if not current_user.is_authenticated():
            return "Must be logged in to log out", 200

        logout_user()
        return "Logged Out", 200
