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
from security_monkey.views import AUDIT_FIELDS
from security_monkey.datastore import ItemAudit
from security_monkey import db
from security_monkey import api

from flask.ext.restful import marshal, reqparse
from flask.ext.login import current_user
import datetime


class JustifyPostDelete(AuthenticatedService):
    def __init__(self):
        super(JustifyPostDelete, self).__init__()

    def post(self, audit_id):
        """
            .. http:post:: /api/1/issues/1234/justification

            Justify an audit issue on a specific item.

            **Example Request**:

            .. sourcecode:: http

                POST /api/1/issues/1234/justification HTTP/1.1
                Host: example.com
                Accept: application/json

                {
                    'justification': 'I promise not to abuse this.'
                }

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 201 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "result": {
                        "justification": "I promise not to abuse this.",
                        "issue": "Example Issue",
                        "notes": "Example Notes",
                        "score": 0,
                        "item_id": 11890,
                        "justified_user": "user@example.com",
                        "justified": true,
                        "justified_date": "2014-06-19 21:45:58.779168",
                        "id": 1234
                    },
                    "auth": {
                        "authenticated": true,
                        "user": "user@example.com"
                    }
                }


            :statuscode 201: no error
            :statuscode 401: Authentication Error. Please Login.
        """
        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        self.reqparse.add_argument('justification', required=False, type=str, help='Must provide justification', location='json')
        args = self.reqparse.parse_args()

        item = ItemAudit.query.filter(ItemAudit.id == audit_id).first()
        if not item:
            return {"Error": "Item with audit_id {} not found".format(audit_id)}, 404

        item.justified_user_id = current_user.id
        item.justified = True
        item.justified_date = datetime.datetime.utcnow()
        item.justification = args['justification']

        db.session.add(item)
        db.session.commit()

        item2 = ItemAudit.query.filter(ItemAudit.id == audit_id).first()

        retdict = {}
        retdict['auth'] = self.auth_dict
        if item2.user:
            retdict['result'] = dict(
                marshal(item2.__dict__, AUDIT_FIELDS).items() +
                {"justified_user": item2.user.email}.items())
        else:
            retdict['result'] = dict(
                marshal(item2.__dict__, AUDIT_FIELDS).items() +
                {"justified_user": None}.items())

        return retdict, 200

    def delete(self, audit_id):
        """
            .. http:delete:: /api/1/issues/1234/justification

            Remove a justification on an audit issue on a specific item.

            **Example Request**:

            .. sourcecode:: http

                DELETE /api/1/issues/1234/justification HTTP/1.1
                Host: example.com
                Accept: application/json


            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 202 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "status": "deleted"
                }


            :statuscode 202: Accepted
            :statuscode 401: Authentication Error. Please Login.
        """
        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        item = ItemAudit.query.filter(ItemAudit.id == audit_id).first()
        if not item:
            return {"Error": "Item with audit_id {} not found".format(audit_id)}, 404

        item.justified_user_id = None
        item.justified = False
        item.justified_date = None
        item.justification = None

        db.session.add(item)
        db.session.commit()

        return {"status": "deleted"}, 202
