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
from flask import request
from marshmallow.validate import OneOf
from werkzeug.exceptions import BadRequest

from security_monkey.views import AuthenticatedService
from security_monkey.views import USER_SETTINGS_FIELDS
from security_monkey.datastore import Account
from security_monkey.datastore import User
from security_monkey import db, rbac

from flask_restful import marshal, abort
from flask_login import current_user
from marshmallow import Schema, fields, ValidationError


class SaveSettingsSchema(Schema):
    accounts = fields.List(fields.Integer())
    daily_audit_email = fields.Boolean(allow_none=True, required=True)
    change_report_setting = fields.String(allow_none=True, required=True, validate=OneOf(["ISSUES", "ALL", "NONE"]))


class UserSettings(AuthenticatedService):
    decorators = [
        rbac.exempt  # Can only get / edit own settings anyway
    ]

    def get(self):
        """
            .. http:get:: /api/1/settings

            Get the settings for the given user.

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/settings HTTP/1.1
                Host: example.com
                Accept: application/json

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "auth": {
                        "authenticated": true,
                        "user": "user@example.com"
                    },
                    "settings": [
                        {
                            "accounts": [
                                1,
                                2,
                                3,
                                6,
                                17,
                                21,
                                22
                            ],
                            "change_reports": "ISSUES",
                            "daily_audit_email": true
                        }
                    ]
                }

            :statuscode 200: no error
            :statuscode 401: Authentication Error. Please Authenticate.
        """

        return_dict = {"auth": self.auth_dict, "settings": []}

        user = User.query.filter(User.id == current_user.get_id()).first()
        if user:
            sub_marshaled = marshal(user.__dict__, USER_SETTINGS_FIELDS)
            account_ids = []
            for account in user.accounts:
                account_ids.append(account.id)
            sub_marshaled = dict(list(sub_marshaled.items()) +
                                 list({"accounts": account_ids}.items())
                                 )
            return_dict["settings"].append(sub_marshaled)
        return return_dict, 200

    def post(self):
        """
            .. http:post:: /api/1/settings

            Change the settings for the current user.

            **Example Request**:

            .. sourcecode:: http

                POST /api/1/settings HTTP/1.1
                Host: example.com
                Accept: application/json

                {
                    "accounts": [
                        1,
                        2,
                        3,
                        6,
                        17,
                        21,
                        22
                    ],
                    "daily_audit_email": true,
                    "change_report_setting": "ALL"
                }

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "auth": {
                        "authenticated": true,
                        "user": "user@example.com"
                    },
                    "settings": {
                        "accounts": [
                            1,
                            2,
                            3,
                            6,
                            17,
                            21,
                            22
                        ],
                        "daily_audit_email": true,
                        "change_report_setting": "ALL"
                    }
                }

            :statuscode 200: no error
            :statuscode 401: Authentication Error. Please Login.
        """
        json_data = request.get_json()
        if not json_data:
            raise BadRequest()

        try:
            args = SaveSettingsSchema(strict=True).load(json_data).data
        except ValidationError as ve:
            abort(400, message=ve.message)

        current_user.daily_audit_email = args['daily_audit_email']
        current_user.change_reports = args['change_report_setting']

        account_list = []
        for account_id in args['accounts']:
            account = Account.query.filter(Account.id == account_id).first()
            if account:
                account_list.append(account)
                #current_user.accounts.append(account)
        current_user.accounts = account_list

        db.session.add(current_user)
        db.session.commit()

        retdict = {'auth': self.auth_dict}
        account_ids = []
        for account in current_user.accounts:
            account_ids.append(account.id)
        retdict['settings'] = {
            "accounts": account_ids,
            "change_report_setting": current_user.change_reports,
            "daily_audit_email": current_user.daily_audit_email
        }

        return retdict, 200
