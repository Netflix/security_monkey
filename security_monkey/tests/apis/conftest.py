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
.. module: security_monkey.tests.apis.conftest
    :platform: Unix
.. version:: $$VERSION$$
.. moduleauthor::  Mike Grima <mgrima@netflix.com>
"""
from os.path import dirname, join

import pytest
import os


@pytest.yield_fixture()
def app():
    import security_monkey
    from security_monkey.factories import setup_app

    # Fix the configuration path:
    path = dirname(__file__)
    path = join(path, 'env-config')
    path = join(path, 'config.py')

    os.environ['SECURITY_MONKEY_SETTINGS'] = path

    # Make a new app:
    app = setup_app(security_monkey.BLUEPRINTS)
    ctx = app.app_context()
    ctx.push()

    security_monkey.app = app

    yield app

    ctx.pop()
    del os.environ['SECURITY_MONKEY_SETTINGS']


@pytest.yield_fixture()
def db(app):
    from security_monkey.extensions import db

    db.drop_all()
    db.create_all()

    from security_monkey.datastore import User, Role

    # Create the Roles and the corresponding users:
    for role in ['Admin', 'Justify', 'Comment', 'View']:
        r = Role()
        r.name = role

        db.session.add(r)
        db.session.commit()

        u = User()
        u.email = "{}@securitymonkey".format(role.lower())
        u.active = True
        u.role = role

        db.session.add(u)
        db.session.commit()

    yield db

    db.drop_all()


# TODO Add a fixture to make some AWS accounts...
