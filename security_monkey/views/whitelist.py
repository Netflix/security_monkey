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

from security_monkey.views import AuthenticatedService
from security_monkey.views import __check_auth__
from security_monkey.views import WHITELIST_FIELDS
from security_monkey.datastore import NetworkWhitelistEntry
from security_monkey import db
from security_monkey import api

from flask.ext.restful import marshal, reqparse


class WhitelistListPost(AuthenticatedService):
    def __init__(self):
        super(WhitelistListPost, self).__init__()

    def get(self):
        """
            .. http:get:: /api/1/whitelistcidrs

            Get a list of CIDR's whitelisted to be used in security groups.

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/whitelistcidrs HTTP/1.1
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
                            "id": 123,
                            "name": "Corp",
                            "notes": "Corporate Network",
                            "cidr": "1.2.3.4/22"
                        },
                    ],
                    total: 1,
                    page: 1,
                    auth: {
                        authenticated: true,
                        user: "user@example.com"
                    }
                }

            :statuscode 200: no error
            :statuscode 401: Authentication failure. Please login.
        """
        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        self.reqparse.add_argument('count', type=int, default=30, location='args')
        self.reqparse.add_argument('page', type=int, default=1, location='args')

        args = self.reqparse.parse_args()
        page = args.pop('page', None)
        count = args.pop('count', None)

        result = NetworkWhitelistEntry.query.order_by(NetworkWhitelistEntry.id).paginate(page, count, error_out=False)

        items = []
        for entry in result.items:
            whitelistentry_marshaled = marshal(entry.__dict__, WHITELIST_FIELDS)
            items.append(whitelistentry_marshaled)

        marshaled_dict = {}
        marshaled_dict['total'] = result.total
        marshaled_dict['count'] = len(items)
        marshaled_dict['page'] = result.page
        marshaled_dict['items'] = items
        marshaled_dict['auth'] = self.auth_dict
        return marshaled_dict, 200

    def post(self):
        """
            .. http:post:: /api/1/whitelistcidrs

            Create a new CIDR whitelist entry.

            **Example Request**:

            .. sourcecode:: http

                POST /api/1/whitelistcidrs HTTP/1.1
                Host: example.com
                Accept: application/json

                {
                    "name": "Corp",
                    "notes": "Corporate Network",
                    "cidr": "1.2.3.4/22"
                }

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 201 Created
                Vary: Accept
                Content-Type: application/json

                {
                    "id": 123,
                    "name": "Corp",
                    "notes": "Corporate Network",
                    "cidr": "1.2.3.4/22"
                }

            :statuscode 201: created
            :statuscode 401: Authentication Error. Please Login.
        """
        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        self.reqparse.add_argument('name', required=True, type=unicode, help='Must provide account name', location='json')
        self.reqparse.add_argument('cidr', required=True, type=unicode, help='Network CIDR required.', location='json')
        self.reqparse.add_argument('notes', required=False, type=unicode, help='Add context.', location='json')
        args = self.reqparse.parse_args()

        name = args['name']
        cidr = args.get('cidr', True)
        notes = args.get('notes', None)

        whitelist_entry = NetworkWhitelistEntry()
        whitelist_entry.name = name
        whitelist_entry.cidr = cidr
        if notes:
            whitelist_entry.notes = notes

        db.session.add(whitelist_entry)
        db.session.commit()

        updated_entry = NetworkWhitelistEntry.query.filter(NetworkWhitelistEntry.id == whitelist_entry.id).first()
        whitelistentry_marshaled = marshal(updated_entry.__dict__, WHITELIST_FIELDS)
        whitelistentry_marshaled['auth'] = self.auth_dict
        return whitelistentry_marshaled, 201


class WhitelistGetPutDelete(AuthenticatedService):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(WhitelistGetPutDelete, self).__init__()

    def get(self, item_id):
        """
            .. http:get:: /api/1/whitelistcidrs/<int:id>

            Get the whitelist entry with the given ID.

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/whitelistcidrs/123 HTTP/1.1
                Host: example.com
                Accept: application/json, text/javascript

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "id": 123,
                    "name": "Corp",
                    "notes": "Corporate Network",
                    "cidr": "1.2.3.4/22",
                    auth: {
                        authenticated: true,
                        user: "user@example.com"
                    }
                }

            :statuscode 200: no error
            :statuscode 404: item with given ID not found
            :statuscode 401: Authentication failure. Please login.
        """
        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        result = NetworkWhitelistEntry.query.filter(NetworkWhitelistEntry.id == item_id).first()

        if not result:
            return {"status": "Whitelist entry with the given ID not found."}, 404

        whitelistentry_marshaled = marshal(result.__dict__, WHITELIST_FIELDS)
        whitelistentry_marshaled['auth'] = self.auth_dict

        return whitelistentry_marshaled, 200

    def put(self, item_id):
        """
            .. http:get:: /api/1/whitelistcidrs/<int:id>

            Update the whitelist entry with the given ID.

            **Example Request**:

            .. sourcecode:: http

                PUT /api/1/whitelistcidrs/123 HTTP/1.1
                Host: example.com
                Accept: application/json, text/javascript

                {
                    "id": 123,
                    "name": "Corp",
                    "notes": "Corporate Network - New",
                    "cidr": "2.2.0.0/16"
                }

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "id": 123,
                    "name": "Corp",
                    "notes": "Corporate Network - New",
                    "cidr": "2.2.0.0/16",
                    auth: {
                        authenticated: true,
                        user: "user@example.com"
                    }
                }

            :statuscode 200: no error
            :statuscode 404: item with given ID not found
            :statuscode 401: Authentication failure. Please login.
        """
        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        self.reqparse.add_argument('name', required=True, type=unicode, help='Must provide account name', location='json')
        self.reqparse.add_argument('cidr', required=True, type=unicode, help='Network CIDR required.', location='json')
        self.reqparse.add_argument('notes', required=False, type=unicode, help='Add context.', location='json')
        args = self.reqparse.parse_args()

        name = args['name']
        cidr = args.get('cidr', True)
        notes = args.get('notes', None)

        result = NetworkWhitelistEntry.query.filter(NetworkWhitelistEntry.id == item_id).first()

        if not result:
            return {"status": "Whitelist entry with the given ID not found."}, 404

        result.name = name
        result.cidr = cidr
        result.notes = notes
        db.session.add(result)
        db.session.commit()

        updated_entry = NetworkWhitelistEntry.query.filter(NetworkWhitelistEntry.id == result.id).first()
        whitelistentry_marshaled = marshal(updated_entry.__dict__, WHITELIST_FIELDS)
        whitelistentry_marshaled['auth'] = self.auth_dict

        return whitelistentry_marshaled, 200

    def delete(self, item_id):
        """
            .. http:delete:: /api/1/whitelistcidrs/123

            Delete a network whitelist entry.

            **Example Request**:

            .. sourcecode:: http

                DELETE /api/1/whitelistcidrs/123 HTTP/1.1
                Host: example.com
                Accept: application/json

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 202 Accepted
                Vary: Accept
                Content-Type: application/json

                {
                    'status': 'deleted'
                }

            :statuscode 202: accepted
            :statuscode 401: Authentication Error. Please Login.
        """
        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        NetworkWhitelistEntry.query.filter(NetworkWhitelistEntry.id == item_id).delete()
        db.session.commit()

        return {'status': 'deleted'}, 202
