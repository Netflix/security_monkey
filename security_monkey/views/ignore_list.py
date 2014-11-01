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
from security_monkey.views import IGNORELIST_FIELDS
from security_monkey.datastore import IgnoreListEntry
from security_monkey.datastore import Technology
from security_monkey import db
from security_monkey import api

from flask.ext.restful import marshal, reqparse


class IgnoreListGetPutDelete(AuthenticatedService):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(IgnoreListGetPutDelete, self).__init__()

    def get(self, item_id):
        """
            .. http:get:: /api/1/ignorelistentries/<int:id>

            Get the ignorelist entry with the given ID.

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/ignorelistentries/123 HTTP/1.1
                Host: example.com
                Accept: application/json, text/javascript

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "id": 123,
                    "prefix": "noisy_",
                    "notes": "Security Monkey shouldn't track noisy_* objects",
                    "technology": "securitygroup",
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

        result = IgnoreListEntry.query.filter(IgnoreListEntry.id == item_id).first()

        if not result:
            return {"status": "Ignorelist entry with the given ID not found."}, 404

        ignorelistentry_marshaled = marshal(result.__dict__, IGNORELIST_FIELDS)
        ignorelistentry_marshaled['technology'] = result.technology.name
        ignorelistentry_marshaled['auth'] = self.auth_dict

        return ignorelistentry_marshaled, 200

    def put(self, item_id):
        """
            .. http:get:: /api/1/ignorelistentries/<int:id>

            Update the ignorelist entry with the given ID.

            **Example Request**:

            .. sourcecode:: http

                PUT /api/1/ignorelistentries/123 HTTP/1.1
                Host: example.com
                Accept: application/json, text/javascript

                {
                    "id": 123,
                    "prefix": "noisy_",
                    "notes": "Security Monkey shouldn't track noisy_* objects",
                    "technology": "securitygroup"
                }

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "id": 123,
                    "prefix": "noisy_",
                    "notes": "Security Monkey shouldn't track noisy_* objects",
                    "technology": "securitygroup",
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

        self.reqparse.add_argument('prefix', required=True, type=unicode, help='A prefix must be provided which matches the objects you wish to ignore.', location='json')
        self.reqparse.add_argument('notes', required=False, type=unicode, help='Add context.', location='json')
        self.reqparse.add_argument('technology', required=True, type=unicode, help='Network CIDR required.', location='json')
        args = self.reqparse.parse_args()

        prefix = args['prefix']
        technology = args.get('technology', True)
        notes = args.get('notes', None)

        result = IgnoreListEntry.query.filter(IgnoreListEntry.id == item_id).first()

        if not result:
            return {"status": "Whitelist entry with the given ID not found."}, 404

        result.prefix = prefix
        result.notes = notes

        technology = Technology.query.filter(Technology.name == technology).first()
        if not technology:
            return {"status": "Could not find a technology with the given name"}, 500

        result.tech_id = technology.id

        db.session.add(result)
        db.session.commit()

        updated_entry = IgnoreListEntry.query.filter(IgnoreListEntry.id == result.id).first()
        whitelistentry_marshaled = marshal(updated_entry.__dict__, IGNORELIST_FIELDS)
        whitelistentry_marshaled['technology'] = updated_entry.technology.name
        whitelistentry_marshaled['auth'] = self.auth_dict

        return whitelistentry_marshaled, 200

    def delete(self, item_id):
        """
            .. http:delete:: /api/1/ignorelistentries/123

            Delete a ignorelist entry.

            **Example Request**:

            .. sourcecode:: http

                DELETE /api/1/ignorelistentries/123 HTTP/1.1
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

        IgnoreListEntry.query.filter(IgnoreListEntry.id == item_id).delete()
        db.session.commit()

        return {'status': 'deleted'}, 202


class IgnorelistListPost(AuthenticatedService):
    def __init__(self):
        super(IgnorelistListPost, self).__init__()

    def get(self):
        """
            .. http:get:: /api/1/ignorelistentries

            Get a list of Ignorelist entries.

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/ignorelistentries HTTP/1.1
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
                            "prefix": "noisy_",
                            "notes": "Security Monkey shouldn't track noisy_* objects",
                            "technology": "securitygroup"
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

        result = IgnoreListEntry.query.order_by(IgnoreListEntry.id).paginate(page, count, error_out=False)

        items = []
        for entry in result.items:
            ignorelistentry_marshaled = marshal(entry.__dict__, IGNORELIST_FIELDS)
            ignorelistentry_marshaled["technology"] = entry.technology.name
            items.append(ignorelistentry_marshaled)

        marshaled_dict = {}
        marshaled_dict['total'] = result.total
        marshaled_dict['count'] = len(items)
        marshaled_dict['page'] = result.page
        marshaled_dict['items'] = items
        marshaled_dict['auth'] = self.auth_dict
        return marshaled_dict, 200

    def post(self):
        """
            .. http:post:: /api/1/ignorelistentries

            Create a new CIDR whitelist entry.

            **Example Request**:

            .. sourcecode:: http

                POST /api/1/ignorelistentries HTTP/1.1
                Host: example.com
                Accept: application/json

                {
                    "prefix": "noisy_",
                    "notes": "Security Monkey shouldn't track noisy_* objects",
                    "technology": "securitygroup"
                }

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 201 Created
                Vary: Accept
                Content-Type: application/json

                {
                    "id": 123,
                    "prefix": "noisy_",
                    "notes": "Security Monkey shouldn't track noisy_* objects",
                    "technology": "securitygroup"
                }

            :statuscode 201: created
            :statuscode 401: Authentication Error. Please Login.
        """
        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        self.reqparse.add_argument('prefix', required=True, type=unicode, help='A prefix must be provided which matches the objects you wish to ignore.', location='json')
        self.reqparse.add_argument('notes', required=False, type=unicode, help='Add context.', location='json')
        self.reqparse.add_argument('technology', required=True, type=unicode, help='Network CIDR required.', location='json')
        args = self.reqparse.parse_args()

        prefix = args['prefix']
        technology = args.get('technology', True)
        notes = args.get('notes', None)

        entry = IgnoreListEntry()
        entry.prefix = prefix

        if notes:
            entry.notes = notes

        technology = Technology.query.filter(Technology.name == technology).first()
        if not technology:
            return {"status": "Could not find a technology with the given name"}, 500

        entry.tech_id = technology.id

        db.session.add(entry)
        db.session.commit()

        updated_entry = IgnoreListEntry.query.filter(IgnoreListEntry.id == entry.id).first()
        ignorelistentry_marshaled = marshal(updated_entry.__dict__, IGNORELIST_FIELDS)
        ignorelistentry_marshaled['technology'] = entry.technology.name
        ignorelistentry_marshaled['auth'] = self.auth_dict
        return ignorelistentry_marshaled, 201
