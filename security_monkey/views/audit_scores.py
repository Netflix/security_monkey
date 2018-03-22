#     Copyright 2016 Bridgewater Associates
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
.. module: security_monkey.views.audit_scores
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from six import text_type

from security_monkey.views import AuthenticatedService
from security_monkey.views import AUDIT_SCORE_FIELDS
from security_monkey.views import ACCOUNT_PATTERN_AUDIT_SCORE_FIELDS
from security_monkey.datastore import ItemAuditScore
from security_monkey import db, rbac

from flask_restful import marshal, reqparse


class AuditScoresGet(AuthenticatedService):
    decorators = [
        rbac.allow(["View"], ["GET"]),
        rbac.allow(["Admin"], ["POST"])
    ]

    def __init__(self):
        super(AuditScoresGet, self).__init__()

    def get(self):
        """
            .. http:get:: /api/1/auditscores

            Get a list of override scores for audit items.

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/auditscores HTTP/1.1
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
                            "method": "check_xxx",
                            "technology": "policy",
                            "score": 1
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

        self.reqparse.add_argument(
            'count', type=int, default=30, location='args')
        self.reqparse.add_argument(
            'page', type=int, default=1, location='args')

        args = self.reqparse.parse_args()
        page = args.pop('page', None)
        count = args.pop('count', None)

        result = ItemAuditScore.query.order_by(ItemAuditScore.technology).paginate(page, count, error_out=False)

        items = []
        for entry in result.items:
            auditscore_marshaled = marshal(entry.__dict__, AUDIT_SCORE_FIELDS)
            items.append(auditscore_marshaled)

        marshaled_dict = {
            'total': result.total,
            'count': len(items),
            'page': result.page,
            'items': items,
            'auth': self.auth_dict
        }

        return marshaled_dict, 200

    def post(self):
        """
            .. http:post:: /api/1/auditscores

            Create a new override audit score.

            **Example Request**:

            .. sourcecode:: http

                POST /api/1/auditscores HTTP/1.1
                Host: example.com
                Accept: application/json

                {
                    "method": "check_xxx",
                    "technology": "policy",
                    "score": 1
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

        self.reqparse.add_argument('method', required=True, type=text_type, help='Must provide method name',
                                   location='json')
        self.reqparse.add_argument('technology', required=True, type=text_type, help='Technology required.',
                                   location='json')
        self.reqparse.add_argument('score', required=False, type=text_type, help='Override score required',
                                   location='json')
        self.reqparse.add_argument('disabled', required=True, type=text_type, help='Disabled flag',
                                   location='json')
        args = self.reqparse.parse_args()

        method = args['method']
        technology = args['technology']
        score = args['score']
        if score is None:
            score = 0
        disabled = args['disabled']

        query = ItemAuditScore.query.filter(ItemAuditScore.technology == technology)
        query = query.filter(ItemAuditScore.method == method)
        auditscore = query.first()

        if not auditscore:
            auditscore = ItemAuditScore()
            auditscore.method = method
            auditscore.technology = technology

        auditscore.score = int(score)
        auditscore.disabled = bool(disabled)

        db.session.add(auditscore)
        db.session.commit()
        db.session.refresh(auditscore)

        auditscore_marshaled = marshal(auditscore.__dict__, AUDIT_SCORE_FIELDS)
        auditscore_marshaled['auth'] = self.auth_dict
        return auditscore_marshaled, 201


class AuditScoreGetPutDelete(AuthenticatedService):
    decorators = [
        rbac.allow(["View"], ["GET"]),
        rbac.allow(["Admin"], ["PUT", "DELETE"])
    ]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(AuditScoreGetPutDelete, self).__init__()

    def get(self, id):
        """
            .. http:get:: /api/1/auditscores/<int:id>

            Get the overide audit score with given ID.

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/auditscores/123 HTTP/1.1
                Host: example.com
                Accept: application/json, text/javascript

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "id": 123,
                    "method": "check_xxx",
                    "technology": "policy",
                    "score": "1",
                    auth: {
                        authenticated: true,
                        user: "user@example.com"
                    }
                }

            :statuscode 200: no error
            :statuscode 404: item with given ID not found
            :statuscode 401: Authentication failure. Please login.
        """

        result = ItemAuditScore.query.filter(ItemAuditScore.id == id).first()

        if not result:
            return {"status": "Override Audit Score with the given ID not found."}, 404

        auditscore_marshaled = marshal(result.__dict__, AUDIT_SCORE_FIELDS)
        auditscore_marshaled['auth'] = self.auth_dict

        account_pattern_scores_marshaled = []
        for account_pattern_score in result.account_pattern_scores:
            account_pattern_score_marshaled = marshal(account_pattern_score, ACCOUNT_PATTERN_AUDIT_SCORE_FIELDS)
            account_pattern_scores_marshaled.append(account_pattern_score_marshaled)
        auditscore_marshaled['account_pattern_scores'] = account_pattern_scores_marshaled

        return auditscore_marshaled, 200

    def put(self, id):
        """
            .. http:get:: /api/1/auditscores/<int:id>

            Update override audit score with the given ID.

            **Example Request**:

            .. sourcecode:: http

                PUT /api/1/auditscores/123 HTTP/1.1
                Host: example.com
                Accept: application/json, text/javascript

                {
                    "id": 123,
                    "method": "check_xxx",
                    "technology": "policy",
                    "Score": "1"
                }

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "id": 123,
                    "score": "1",
                    auth: {
                        authenticated: true,
                        user: "user@example.com"
                    }
                }

            :statuscode 200: no error
            :statuscode 404: item with given ID not found
            :statuscode 401: Authentication failure. Please login.
        """

        self.reqparse.add_argument('method', required=True, type=text_type, help='Must provide method name',
                                   location='json')
        self.reqparse.add_argument('technology', required=True, type=text_type, help='Technology required.',
                                   location='json')
        self.reqparse.add_argument('score', required=False, type=text_type, help='Must provide score.',
                                   location='json')
        self.reqparse.add_argument('disabled', required=True, type=text_type, help='Must disabled flag.',
                                   location='json')

        args = self.reqparse.parse_args()

        score = args['score']
        if score is None:
            score = 0

        result = ItemAuditScore.query.filter(ItemAuditScore.id == id).first()

        if not result:
            return {"status": "Override audit score with the given ID not found."}, 404

        result.method = args['method']
        result.technology = args['technology']
        result.disabled = args['disabled']
        result.score = int(score)

        db.session.add(result)
        db.session.commit()
        db.session.refresh(result)

        auditscore_marshaled = marshal(result.__dict__, AUDIT_SCORE_FIELDS)
        auditscore_marshaled['auth'] = self.auth_dict

        return auditscore_marshaled, 200

    def delete(self, id):
        """
            .. http:delete:: /api/1/auditscores/123

            Delete an override audit score

            **Example Request**:

            .. sourcecode:: http

                DELETE /api/1/auditscores/123 HTTP/1.1
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

        result = ItemAuditScore.query.filter(ItemAuditScore.id == id).first()

        db.session.delete(result)
        db.session.commit()

        return {'status': 'deleted'}, 202
