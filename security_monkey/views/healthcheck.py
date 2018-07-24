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
.. module: security_monkey.views.healthcheck
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""
from flask import Blueprint
from security_monkey.extensions import db

mod = Blueprint('healthcheck', __name__)


# Code shamelessly copypasta'd from Lemur
@mod.route('/healthcheck')
def health():
    try:
        if healthcheck(db):
            return 'ok'
    except Exception:
        return 'DB check failed'


def healthcheck(db):
    with db.engine.connect() as connection:
        connection.execute('SELECT 1;')
    return True
