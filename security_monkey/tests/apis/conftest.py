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
def app(request):
    # request is from pytest. Needed for tests with Flask.
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

    db.session.close()
    db.drop_all()


@pytest.yield_fixture()
def user_tokens(db):
    from security_monkey.auth.service import create_token
    from security_monkey.datastore import User

    users = User.query.all()

    return {u.email: create_token(u) for u in users}


@pytest.yield_fixture()
def session(db, request):
    """
    Creates a new database session with (with working transaction)
    for test duration.
    """
    db.session.begin_nested()
    yield db.session
    db.session.rollback()


@pytest.yield_fixture()
def account_type_aws(db):
    from security_monkey.datastore import AccountType

    aws = AccountType(name="AWS")

    db.session.add(aws)
    db.session.commit()

    return aws


@pytest.yield_fixture()
def test_aws_accounts(db, account_type_aws):
    from security_monkey.datastore import Account

    active_account_one = Account(active=True, third_party=False, name="ActiveOne",
                                 notes="Active test account 1.", identifier="111111111111",
                                 account_type_id=account_type_aws.id)

    active_account_two = Account(active=True, third_party=False, name="ActiveTwo",
                                 notes="Active test account 2.", identifier="222222222222",
                                 account_type_id=account_type_aws.id)

    third_party_one = Account(active=False, third_party=True, name="3rdPartyOne",
                              notes="3rd Party account 1.", identifier="333333333333",
                              account_type_id=account_type_aws.id)

    third_party_two = Account(active=False, third_party=True, name="3rdPartyTwo",
                              notes="3rd Party account 2.", identifier="444444444444",
                              account_type_id=account_type_aws.id)

    inactive = Account(active=False, third_party=False, name="Inactive",
                       notes="Inactive account", identifier="555555555555",
                       account_type_id=account_type_aws.id)

    db.session.add(active_account_one)
    db.session.add(active_account_two)
    db.session.add(third_party_one)
    db.session.add(third_party_two)
    db.session.add(inactive)
    db.session.commit()

    return {
        active_account_one.name: active_account_one,
        active_account_two.name: active_account_two,
        third_party_one.name: third_party_one,
        third_party_two.name: third_party_two,
        inactive.name: inactive
    }
