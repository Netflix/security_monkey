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
from json import JSONDecodeError

from marshmallow import Schema, fields, ValidationError
from marshmallow.validate import OneOf, Length

from security_monkey.auth.permissions import admin_permission
from security_monkey.exceptions import AccountNameExists, AccountIdentifierExists
from security_monkey.auth.service import AuthenticatedService
from security_monkey.datastore import Account, AccountType
from security_monkey.account_manager import get_account_by_id, delete_account_by_id, AccountManager, \
    load_all_account_types
from security_monkey.common.audit_issue_cleanup import clean_account_issues
from security_monkey.extensions import db

from flask import current_app, Blueprint, request
from flask_restful import Api

from security_monkey.views import PaginationSchema

mod = Blueprint('account', __name__)
api = Api(mod)


class AccountSchema(Schema):
    """Schema to describe an Account."""

    name = fields.Str(required=True)
    account_type = fields.Str(required=True)
    identifier = fields.Str(required=True)
    id = fields.Int(dump_only=True, required=True)
    third_party = fields.Bool(required=True)
    active = fields.Bool(required=True)
    custom_fields = fields.Dict(requrired=False)
    notes = fields.Str(default=None)


class BulkAccountUpdateSchema(Schema):
    """Defines the fields that can be updated in bulk. The identifer is used to idenfity
    which account is getting updated.
    """

    identifier = fields.Str(required=True)
    active = fields.Bool(required=True)
    notes = fields.Str(required=False, missing=None, default=None)


class BulkAccountsSchema(Schema):
    """Schema for bulk account updates."""

    accounts = fields.Nested(BulkAccountUpdateSchema, many=True, validate=Length(min=1, max=100), load_only=True)


class AccountSearchSchema(PaginationSchema):
    """Schema for the Search account API. Paginated."""

    order_by = fields.Str(required=False)
    order_dir = fields.Str(required=False, default='desc', missing='desc', validate=OneOf(['asc', 'desc']))
    active = fields.Bool(required=False)
    third_party = fields.Bool(required=False)
    items = fields.Nested(AccountSchema, many=True, dump_only=True)


ACCOUNT_SCHEMA = AccountSchema(strict=True)
BA_SCHEMA = BulkAccountsSchema(strict=True)
ACCOUNT_SEARCH_SCHEMA = AccountSearchSchema(strict=True)


class AccountGetPutDelete(AuthenticatedService):
    def __init__(self):
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
            return {'error': f'Account with ID: {account_id} not found'}, 404

        return ACCOUNT_SCHEMA.dump(result.get_dict()).data, 200

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
        # Parse the account details:
        try:
            args = ACCOUNT_SCHEMA.loads(request.data).data
        except ValidationError as ve:
            current_app.logger.exception(ve)
            return {'Error': f"Invalid request: {str(ve)}"}, 400
        except JSONDecodeError as jde:
            current_app.logger.exception(jde)
            return {'Error': 'Invalid or missing JSON was sent.'}, 400

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
            return {'error': f"Invalid account type. Must be one of: {', '.join(valid_types)}"}, 400

        try:
            account = account_manager.update(account_id, account_type, name, active, third_party, notes, identifier,
                                             custom_fields=custom_fields)
        except AccountNameExists as _:
            return {'error': 'Conflict: Account name already exists.'}, 409

        except AccountIdentifierExists as _:
            return {'error': 'Conflict: Account identifier already exists.'}, 409

        if not account:
            return {'error': f'Account with ID: {account_id} not found'}, 404

        clean_account_issues(account)

        return ACCOUNT_SCHEMA.dump(account.get_dict()).data, 200

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
            :statuscode 400: Invalid request
            :statuscode 409: Account already exists
            :statuscode 401: Authentication Error. Please Login.
        """
        # Parse the account details:
        try:
            args = ACCOUNT_SCHEMA.loads(request.data).data
        except ValidationError as ve:
            current_app.logger.exception(ve)
            return {'Error': f"Invalid request: {str(ve)}"}, 400
        except JSONDecodeError as jde:
            current_app.logger.exception(jde)
            return {'Error': 'Invalid or missing JSON was sent.'}, 400

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
            return {'error': f"Invalid account type. Must be one of: {', '.join(valid_types)}"}, 400

        account = account_manager.create(account_type, name, active, third_party, notes, identifier,
                                         custom_fields=custom_fields)

        if not account:
            return {'error': 'Account already exists.'}, 409

        return ACCOUNT_SCHEMA.dump(account.get_dict()).data, 201

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
            :statuscode 400: Invalid Request
            :statuscode 401: Authentication failure. Please login.
        """
        # Parse the account details:
        try:
            args = ACCOUNT_SEARCH_SCHEMA.loads(request.data).data
        except ValidationError as ve:
            current_app.logger.exception(ve)
            return {'Error': f"Invalid request: {str(ve)}"}, 400
        except JSONDecodeError:
            args = {}

        page = args.pop('page', 1)
        count = args.pop('count', 30)
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
            items.append(account.get_dict())

        result_dict = {
            'total': result.total,
            'count': len(items),
            'page': result.page,
            'items': items,
        }

        return ACCOUNT_SEARCH_SCHEMA.dump(result_dict).data, 200


class AccountListPut(AuthenticatedService):

    def __init__(self):
        super(AccountListPut, self).__init__()

    @admin_permission.require(http_exception=403)
    def put(self):
        """
            .. http:put:: /api/1/accounts_bulk

            Create a new account.

            **Example Request**:

            .. sourcecode:: http

                POST /api/1/accounts/ HTTP/1.1
                Host: example.com
                Accept: application/json
                {
                    "accounts": [
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
                        },
                        ...
                    ]
                }

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200
                Vary: Accept
                Content-Type: application/json
                {
                    "status": "updated"
                }

            :statuscode 200: Updated
            :statuscode 400: Invalid Request
            :statuscode 401: Authentication Error. Please Login.

        :return:
        """
        # Parse the account details:
        try:
            args = BA_SCHEMA.loads(request.data).data
        except ValidationError as ve:
            current_app.logger.exception(ve)
            return {'Error': f"Invalid request: {str(ve)}"}, 400
        except JSONDecodeError as jde:
            current_app.logger.exception(jde)
            return {'Error': 'Invalid or missing JSON was sent.'}, 400

        for account_dict in args['accounts']:
            account = Account.query.filter(Account.identifier == account_dict['identifier']).first()

            if not account:
                return {'error': f'Account with name: {name} not found'}, 404

            notes = account_dict.pop('notes')
            active = account_dict.pop('active')

            account.notes = notes
            account.active = active

            clean_account_issues(account)

            db.session.add(account)

        db.session.commit()

        return {'status': 'updated'}, 200


class AccountConfigGet(AuthenticatedService):

    def __init__(self):
        super(AccountConfigGet, self).__init__()

    def get(self):
        """
            .. http:get:: /api/1/account_config_fields

            Get a list of Account types

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/account_config/all HTTP/1.1
                Host: example.com
                Accept: application/json, text/javascript

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "AWS": {
                        "identifier_label": "Number",
                        "identifier_tool_tip": "Enter the AWS account number, if you have it. (12 digits)",
                        "fields": [
                            {
                                "name": "identifier",
                                "label": "",
                                "editable": True,
                                "tool_tip": "",
                                "password": False,
                                "allowed_values": null
                            },
                            {
                                "name": "name",
                                "label": "",
                                "editable": True,
                                "tool_tip": "",
                                "password": False,
                                "allowed_values": null
                            },
                            ...
                        ]
                    },
                    ...
                }

            :statuscode 200: All possible account config values
            :statuscode 401: Authentication failure. Please login.
        """
        load_all_account_types()

        account_types = AccountType.query.all()
        all_configs = {}

        for account_type in account_types:
            acc_manager = AccountManager.get_registry().get(account_type.name)
            if acc_manager is not None:
                values = {'identifier_label': acc_manager.identifier_label,
                          'identifier_tool_tip': acc_manager.identifier_tool_tip}

                # Common fields:
                fields = [
                    {
                        'name': 'identifier',
                        'label': '',
                        'editable': True,
                        'tool_tip': '',
                        'password': False,
                        'allowed_values': None
                    },
                    {
                        'name': 'name',
                        'label': '',
                        'editable': True,
                        'tool_tip': '',
                        'password': False,
                        'allowed_values': None
                    },
                    {
                        'name': 'notes',
                        'label': '',
                        'editable': True,
                        'tool_tip': '',
                        'password': False,
                        'allowed_values': None
                    }
                ]

                # Custom fields:
                for config in acc_manager.custom_field_configs:
                    fields.append(
                        {
                            'name': config.name,
                            'label': config.label,
                            'editable': config.db_item,
                            'tool_tip': config.tool_tip,
                            'password': config.password,
                            'allowed_values': config.allowed_values
                        }
                    )

                values['fields'] = fields
                all_configs[account_type.name] = values

        return all_configs, 200


api.add_resource(AccountGetPutDelete, '/account/<int:account_id>')
api.add_resource(AccountPostList, '/accounts')
api.add_resource(AccountListPut, '/accounts_bulk')
api.add_resource(AccountConfigGet, '/account_config_fields')
