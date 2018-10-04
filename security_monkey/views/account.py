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
.. module: security_monkey.views.account
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity
.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""
from security_monkey.auth.permissions import admin_permission
from security_monkey.exceptions import AccountNameExists, AccountIdentifierExists
from security_monkey.auth.service import AuthenticatedService
from security_monkey.views import ACCOUNT_FIELDS
from security_monkey.datastore import Account, AccountType
from security_monkey.account_manager import get_account_by_id, delete_account_by_id, AccountManager
from security_monkey.common.audit_issue_cleanup import clean_account_issues

from flask import Blueprint
from flask_restful import marshal, reqparse, Api, inputs

mod = Blueprint('account', __name__)
api = Api(mod)


class AccountGetPutDelete(AuthenticatedService):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(AccountGetPutDelete, self).__init__()

    def get(self, account_id):
        """
            .. http:get:: /api/1/account/<int:id>

            Get a list of Accounts matching the given criteria

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/account/1 HTTP/1.1
                Host: example.com
                Accept: application/json, text/javascript

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "third_party": false,
                    "name": "example_name",
                    "notes": null,
                    "identifier": "111111111111",
                    "active": true,
                    "id": 1,
                    "account_type": "AWS",
                    "custom_fields": {
                        "s3_name": "example_name",
                        "canonical_id": "somecanonicalidhere",
                        "role_name": null
                    }
                }

            :statuscode 200: no error
            :statuscode 404: no account with ID found.
            :statuscode 401: Authentication failure. Please login.
        """
        result = get_account_by_id(account_id)

        if not result:
            return {"error": "Account with ID: {} not found".format(account_id)}, 404

        account_marshaled = marshal(result.get_dict(), ACCOUNT_FIELDS)

        return account_marshaled, 200

    @admin_permission.require(http_exception=403)
    def put(self, account_id):
        """
            .. http:put:: /api/1/account/1

            Edit an existing account.

            **Example Request**:

            .. sourcecode:: http

                PUT /api/1/account/1 HTTP/1.1
                Host: example.com
                Accept: application/json

                {
                    "name": "edited_account"
                    "identifier": "0123456789",
                    "notes": "this account is for ...",
                    "active": true,
                    "third_party": false
                }

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "name": "edited_account"
                    "identifier": "0123456789",
                    "notes": "this account is for ...",
                    "active": true,
                    "third_party": false
                    "account_type": "AWS",
                    "custom_fields": {
                        "s3_name": "example_name",
                        "canonical_id": "somecanonicalidhere",
                        "role_name": null
                    }
                }

            :statuscode 200: no error
            :statuscode 409: Account name or identifier already exists
            :statuscode 401: Authentication Error. Please Login.
        """
        self.reqparse.add_argument('name', type=str, required=True)
        self.reqparse.add_argument('identifier', type=str, required=True)
        self.reqparse.add_argument('account_type', type=str, required=True)
        self.reqparse.add_argument('notes', type=str)
        self.reqparse.add_argument('active', type=inputs.boolean)
        self.reqparse.add_argument('third_party', type=inputs.boolean)
        self.reqparse.add_argument('custom_fields', type=dict)

        args = self.reqparse.parse_args()

        name = args.pop('name')
        identifier = args.pop('identifier')
        account_type = args.pop('account_type')
        notes = args.pop('notes', None)
        active = args.pop('active')
        third_party = args.pop('third_party')
        custom_fields = args.pop('custom_fields', {})

        account_manager = AccountManager.get_registry().get(account_type)

        if not account_manager:
            valid_types = AccountManager.get_registry().keys()
            return {'error': 'Invalid account type. Must be one of: {}'.format(', '.join(valid_types))}, 400

        try:
            account = account_manager.update(account_id, account_type, name, active, third_party, notes, identifier,
                                             custom_fields=custom_fields)
        except AccountNameExists as _:
            return {'error': 'Conflict: Account name already exists.'}, 409

        except AccountIdentifierExists as _:
            return {'error': 'Conflict: Account identifier already exists.'}, 409

        if not account:
            return {'error': "Account with ID: {} not found".format(account_id)}, 404

        clean_account_issues(account)

        marshaled_account = marshal(account.get_dict(), ACCOUNT_FIELDS)

        return marshaled_account, 200

    @admin_permission.require(http_exception=403)
    def delete(self, account_id):
        """
            .. http:delete:: /api/1/account/1

            Delete an account.

            **Example Request**:

            .. sourcecode:: http

                DELETE /api/1/account/1 HTTP/1.1
                Host: example.com
                Accept: application/json

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 202 Accepted
                Vary: Accept
                Content-Type: application/json

                {
                    "status": "deleted"
                }

            :statuscode 202: accepted
            :statuscode 401: Authentication Error. Please Login.
        """
        delete_account_by_id(account_id)
        return {'status': 'deleted'}, 202


class AccountPostList(AuthenticatedService):
    def __init__(self):
        super(AccountPostList, self).__init__()
        self.reqparse = reqparse.RequestParser()

    @admin_permission.require(http_exception=403)
    def post(self):
        """
            .. http:post:: /api/1/accounts/

            Create a new account.

            **Example Request**:

            .. sourcecode:: http

                POST /api/1/accounts/ HTTP/1.1
                Host: example.com
                Accept: application/json

                {
                    "name": "new_account"
                    "identifier": "0123456789",
                    "notes": "this account is for ...",
                    "active": true,
                    "third_party": false
                    "account_type": "AWS",
                    "custom_fields": {
                        "canonical_id": "somecanonicalidhere"
                    }
                }

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 201 Created
                Vary: Accept
                Content-Type: application/json

                {
                    "name": "new_account"
                    "identifier": "0123456789",
                    "notes": "this account is for ...",
                    "active": true,
                    "third_party": false
                    "account_type": "AWS",
                    "custom_fields": {
                        "s3_name": "example_name",
                        "canonical_id": "somecanonicalidhere",
                        "role_name": null
                    }
                }

            :statuscode 201: Created
            :statuscode 409: Account already exists
            :statuscode 401: Authentication Error. Please Login.
        """
        self.reqparse.add_argument('name', type=str, required=True)
        self.reqparse.add_argument('identifier', type=str, required=True)
        self.reqparse.add_argument('account_type', type=str, required=True)
        self.reqparse.add_argument('notes', type=str)
        self.reqparse.add_argument('active', type=inputs.boolean)
        self.reqparse.add_argument('third_party', type=inputs.boolean)
        self.reqparse.add_argument('custom_fields', type=dict)

        args = self.reqparse.parse_args()

        name = args.pop('name')
        identifier = args.pop('identifier')
        account_type = args.pop('account_type')
        notes = args.pop('notes', None)
        active = args.pop('active')
        third_party = args.pop('third_party')
        custom_fields = args.pop('custom_fields', {})

        account_manager = AccountManager.get_registry().get(account_type)

        if not account_manager:
            valid_types = AccountManager.get_registry().keys()
            return {'error': 'Invalid account type. Must be one of: {}'.format(', '.join(valid_types))}, 400

        account = account_manager.create(account_type, name, active, third_party, notes, identifier,
                                         custom_fields=custom_fields)

        if not account:
            return {'error': 'Account already exists.'}, 409

        marshaled_account = marshal(account.get_dict(), ACCOUNT_FIELDS)
        return marshaled_account, 201

    def get(self):
        """
            .. http:get:: /api/1/accounts

            Get a list of Accounts matching the given criteria

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/accounts HTTP/1.1
                Host: example.com
                Accept: application/json, text/javascript

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    count: 1,
                    items: [
                        {

                            "third_party": false,
                            "name": "example_name",
                            "notes": null,
                            "identifier": "111111111111",
                            "active": true,
                            "id": 1,
                            "custom_fields": {
                                "s3_name": "example_name",
                                "canonical_id": "somecanonicalidhere",
                                "role_name": null
                            }
                        },
                    ],
                    total: 1,
                    page: 1
                }

            :statuscode 200: no error
            :statuscode 401: Authentication failure. Please login.
        """

        self.reqparse.add_argument('count', type=int, default=30, location='args')
        self.reqparse.add_argument('page', type=int, default=1, location='args')
        self.reqparse.add_argument('order_by', type=str, location='args')
        self.reqparse.add_argument('order_dir', type=str, default='desc', location='args')
        self.reqparse.add_argument('active', type=inputs.boolean, location='args')
        self.reqparse.add_argument('third_party', type=inputs.boolean, location='args')

        args = self.reqparse.parse_args()
        page = args.pop('page', None)
        count = args.pop('count', None)
        order_by = args.pop('order_by', None)
        order_dir = args.pop('order_dir', None)
        active = args.pop('active', None)
        third_party = args.pop('third_party', None)
        query = Account.query

        if active is not None:
            query = query.filter(Account.active == active)
        if third_party is not None:
            query = query.filter(Account.third_party == third_party)

        if order_by and hasattr(Account, order_by):
            if order_dir.lower() == 'asc':
                if order_by == 'account_type':
                    query = query.join(Account.account_type).order_by(getattr(AccountType, 'name').asc())
                else:
                    query = query.order_by(getattr(Account, order_by).asc())
            else:
                if order_by == 'account_type':
                    query = query.join(Account.account_type).order_by(getattr(AccountType, 'name').desc())
                else:
                    query = query.order_by(getattr(Account, order_by).desc())
        else:
            query = query.order_by(Account.id)

        result = query.paginate(page, count, error_out=False)

        items = []
        for account in result.items:
            account_marshaled = marshal(account.get_dict(), ACCOUNT_FIELDS)

            account_marshaled.update({'account_type': account.account_type.name}.items())

            items.append(account_marshaled)

        marshaled_dict = {
            'total': result.total,
            'count': len(items),
            'page': result.page,
            'items': items,
        }

        return marshaled_dict, 200


api.add_resource(AccountGetPutDelete, '/account/<int:account_id>')
api.add_resource(AccountPostList, '/accounts')
