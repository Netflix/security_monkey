#    Copyright 2017 Bridgewater Associates
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
.. module: security_monkey.views.account_pattern_audit_score
    :platform: Unix
    :synopsis: Manages restful view for account pattern audit scores

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>

"""
from six import text_type

from security_monkey.views import AuthenticatedService
from security_monkey.views import ACCOUNT_PATTERN_AUDIT_SCORE_FIELDS
from security_monkey.datastore import AccountPatternAuditScore
from security_monkey.datastore import ItemAuditScore
from security_monkey import db, app, rbac

from flask_restful import marshal, reqparse


class AccountPatternAuditScoreGet(AuthenticatedService):
    decorators = [
        rbac.allow(["View"], ["GET"]),
    ]

    def __init__(self):
        super(AccountPatternAuditScoreGet, self).__init__()

    def get(self, auditscores_id):
        """
            .. http:get:: /api/1/auditscores/<int:auditscores_id>/accountpatternauditscores

            Get a list of override scores for account pattern audit scores.

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/auditscores/123/accountpatternauditscores HTTP/1.1
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
                            "id": 234,
                            "account_pattern": "AccountPattern",
                            "score": 8,
                            itemauditscores_id: 123
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

        result = ItemAuditScore.query.filter(
            ItemAuditScore.id == auditscores_id).first()

        if not result:
            return {"status": "Override Audit Score with the given ID not found."}, 404

        self.reqparse.add_argument(
            'count', type=int, default=30, location='args')
        self.reqparse.add_argument(
            'page', type=int, default=1, location='args')

        args = self.reqparse.parse_args()
        page = args.pop('page', None)
        count = args.pop('count', None)

        result = AccountPatternAuditScore.query.paginate(
            page, count, error_out=False)

        items = []
        for entry in result.items:
            accountpatternauditscore_marshaled = marshal(
                entry.__dict__, ACCOUNT_PATTERN_AUDIT_SCORE_FIELDS)
            items.append(accountpatternauditscore_marshaled)

        marshaled_dict = {
            'total': result.total,
            'count': len(items),
            'page': result.page,
            'items': items,
            'auth': self.auth_dict
        }

        return marshaled_dict, 200


class AccountPatternAuditScorePost(AuthenticatedService):
    decorators = [
        rbac.allow(["Admin"], ["POST"])
    ]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(AccountPatternAuditScorePost, self).__init__()

    def post(self):
        """
            .. http:post:: /api/1/accountpatternauditscores

            Create a new override account pattern audit score.

            **Example Request**:

            .. sourcecode:: http

                POST /api/1/accountpatternauditscores HTTP/1.1
                Host: example.com
                Accept: application/json

                {
                    "account_pattern": "AccountPattern",
                    "score": 8,
                    "itemauditscores_id": 123
                }

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 201 Created
                Vary: Accept
                Content-Type: application/json

                {
                    "id": 234,
                    "account_pattern": "AccountPattern",
                    "score": 8,
                    "itemauditscores_id": 123
                }

            :statuscode 201: created
            :statuscode 401: Authentication Error. Please Login.
        """

        self.reqparse.add_argument('account_type', required=False, type=text_type, location='json')
        self.reqparse.add_argument('account_field', required=True, type=text_type, help='Must provide account field',
                                   location='json')
        self.reqparse.add_argument('account_pattern', required=True, type=text_type, help='Must provide account pattern',
                                   location='json')
        self.reqparse.add_argument('score', required=True, type=text_type, help='Override score required',
                                   location='json')
        self.reqparse.add_argument('itemauditscores_id', required=True, type=text_type, help='Audit Score ID required',
                                   location='json')
        args = self.reqparse.parse_args()

        result = ItemAuditScore.query.filter(
            ItemAuditScore.id == args['itemauditscores_id']).first()

        if not result:
            return {"status": "Audit Score ID not found."}, 404

        result.add_or_update_pattern_score(args['account_type'], args['account_field'],
                                           args['account_pattern'], int(args['score']))
        db.session.commit()
        db.session.refresh(result)

        accountpatternauditscore = result.get_account_pattern_audit_score(args['account_type'],
                                                                          args['account_field'],
                                                                          args['account_pattern'])


        accountpatternauditscore_marshaled = marshal(accountpatternauditscore.__dict__,
                                                     ACCOUNT_PATTERN_AUDIT_SCORE_FIELDS)
        accountpatternauditscore_marshaled['auth'] = self.auth_dict
        return accountpatternauditscore_marshaled, 201


class AccountPatternAuditScoreGetPutDelete(AuthenticatedService):
    decorators = [
        rbac.allow(["View"], ["GET"]),
        rbac.allow(["Admin"], ["PUT", "DELETE"])
    ]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(AccountPatternAuditScoreGetPutDelete, self).__init__()

    def get(self, id):
        """
            .. http:get:: /api/1/accountpatternauditscores/<int:id>

            Get the overide account pattern audit score with given ID.

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/accountpatternauditscores/234 HTTP/1.1
                Host: example.com
                Accept: application/json, text/javascript

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "id": 234,
                    "account_pattern": "AccountPattern",
                    "score": 8,
                    "itemauditscores_id": 123
                    auth: {
                        authenticated: true,
                        user: "user@example.com"
                    }
                }

            :statuscode 200: no error
            :statuscode 404: item with given ID not found
            :statuscode 401: Authentication failure. Please login.
        """

        app.logger.info('ID: ' + str(id))

        result = AccountPatternAuditScore.query.filter(
            AccountPatternAuditScore.id == id).first()
        if not result:
            return {"status": "Override Account Pattern Audit Score with the given ID not found."}, 404

        app.logger.info('RESULT DICT: ' + str(result.__dict__))

        accountpatternauditscore_marshaled = marshal(
            result.__dict__, ACCOUNT_PATTERN_AUDIT_SCORE_FIELDS)
        accountpatternauditscore_marshaled['auth'] = self.auth_dict

        app.logger.info('RETURN: ' + str(accountpatternauditscore_marshaled))

        return accountpatternauditscore_marshaled, 200

    def put(self, id):
        """
            .. http:put:: /api/1/accountpatternauditscores/<int:id>

            Update override account pattern audit score with the given ID.

            **Example Request**:

            .. sourcecode:: http

                PUT /api/1/accountpatternauditscores/234 HTTP/1.1
                Host: example.com
                Accept: application/json, text/javascript

                {
                    "id": 234,
                    "account_pattern": "AccountPattern",
                    "score": 5
                }

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "id": 234,
                    "account_pattern": "AccountPattern"
                    "score": 5,
                    "itemauditscores_id": 123
                    auth: {
                        authenticated: true,
                        user: "user@example.com"
                    }
                }

            :statuscode 200: no error
            :statuscode 404: item with given ID not found
            :statuscode 401: Authentication failure. Please login.
        """

        self.reqparse.add_argument('account_type', required=False, type=text_type,
                                   help='Must provide account type.', location='json')
        self.reqparse.add_argument('account_field', required=False, type=text_type,
                                   help='Must provide account field.', location='json')
        self.reqparse.add_argument('account_pattern', required=False, type=text_type,
                                   help='Must provide account pattern.', location='json')
        self.reqparse.add_argument(
            'score', required=False, type=text_type, help='Must provide score.', location='json')
        args = self.reqparse.parse_args()

        result = AccountPatternAuditScore.query.filter(
            AccountPatternAuditScore.id == id).first()
        if not result:
            return {"status": "Override Account Pattern Audit Score with the given ID not found."}, 404

        result.account_type = args['account_type']
        result.account_field = args['account_field']
        result.account_pattern = args['account_pattern']
        result.score = int(args['score'])

        db.session.add(result)
        db.session.commit()
        db.session.refresh(result)

        accountpatternauditscore_marshaled = marshal(
            result.__dict__, ACCOUNT_PATTERN_AUDIT_SCORE_FIELDS)
        accountpatternauditscore_marshaled['auth'] = self.auth_dict

        return accountpatternauditscore_marshaled, 200

    def delete(self, id):
        """
            .. http:delete:: /api/1/accountpatternauditscores/<int:id>

            Delete an override account pattern audit score

            **Example Request**:

            .. sourcecode:: http

                DELETE /api/1/accountpatternauditscores/234 HTTP/1.1
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

        AccountPatternAuditScore.query.filter(
            AccountPatternAuditScore.id == id).delete()
        db.session.commit()

        return {'status': 'deleted'}, 202
