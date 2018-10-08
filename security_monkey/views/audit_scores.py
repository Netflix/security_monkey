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
from json import JSONDecodeError

from flask import Blueprint, request, current_app
from marshmallow import Schema, fields, ValidationError
from marshmallow.validate import Range

from security_monkey.auth.permissions import admin_permission
from security_monkey.auth.service import AuthenticatedService
from security_monkey.views import PaginationSchema
from security_monkey.datastore import ItemAuditScore

from security_monkey.extensions import db

from flask_restful import Api

mod = Blueprint('auditscores', __name__)
api = Api(mod)


class AuditItemScoreSchema(Schema):
    """Schema that describes an Audit Item Score Override."""

    id = fields.Int(dump_only=True)
    method = fields.Str(required=True)
    technology = fields.Str(required=True)
    score = fields.Int(required=True, validate=Range(min=0))
    disabled = fields.Boolean(required=True)


class ListAuditScoresSchema(PaginationSchema):
    """Schema for the List Audit Scores API."""

    items = fields.Nested(AuditItemScoreSchema, dump_only=True, many=True)


AUDIT_ITEM_SCORE_SCHEMA = AuditItemScoreSchema(strict=True)
LIST_AUDIT_SCORES_SCHEMA = ListAuditScoresSchema(strict=True)


class AuditScoresGet(AuthenticatedService):
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
                            "score": 1,
                            "disabled": false
                        },
                    ],
                    total: 1,
                    page: 1
                }

            :statuscode 200: no error
            :statuscode 401: Authentication failure. Please login.
        """
        try:
            args = LIST_AUDIT_SCORES_SCHEMA.loads(request.data).data
        except ValidationError as ve:
            current_app.logger.exception(ve)
            return {'Error': f"Invalid request: {str(ve)}"}, 400
        except JSONDecodeError:
            args = {}

        count = args.pop('count', 30)
        page = args.pop('page', 1)

        result = ItemAuditScore.query.order_by(ItemAuditScore.technology).paginate(page, count, error_out=False)

        items = []
        for entry in result.items:
            items.append(entry.__dict__)

        result_dict = {
            'total': result.total,
            'count': len(items),
            'page': result.page,
            'items': items
        }

        return LIST_AUDIT_SCORES_SCHEMA.dump(result_dict).data, 200

    @admin_permission.require(http_exception=403)
    def post(self):
        """
            .. http:post:: /api/1/auditscores

            Create a new override audit score -- or update an existing one (unique on method and technology).

            **Example Request**:

            .. sourcecode:: http

                POST /api/1/auditscores HTTP/1.1
                Host: example.com
                Accept: application/json

                {
                    "method": "check_xxx",
                    "technology": "policy",
                    "disabled": false,
                    "score": 1
                }

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 201 Created
                Vary: Accept
                Content-Type: application/json

                {
                    "id": 123,
                    "method": "check_xxx",
                    "technology": "policy",
                    "disabled": false,
                    "score": 1
                }

            :statuscode 201: created
            :statuscode 401: Authentication Error. Please Login.
        """
        # Parse the audit score override details:
        try:
            args = AUDIT_ITEM_SCORE_SCHEMA.loads(request.data).data
        except ValidationError as ve:
            current_app.logger.exception(ve)
            return {'Error': f"Invalid request: {str(ve)}"}, 400
        except JSONDecodeError as jde:
            current_app.logger.exception(jde)
            return {'Error': 'Invalid or missing JSON was sent.'}, 400

        method = args['method']
        technology = args['technology']
        score = args['score']
        disabled = args['disabled']

        auditscore = ItemAuditScore.query.filter(ItemAuditScore.technology == technology,
                                                 ItemAuditScore.method == method).first()

        if not auditscore:
            auditscore = ItemAuditScore(method=method, technology=technology)

        auditscore.score = int(score)
        auditscore.disabled = bool(disabled)

        db.session.add(auditscore)
        db.session.commit()
        db.session.refresh(auditscore)

        return AUDIT_ITEM_SCORE_SCHEMA.dump(auditscore.__dict__).data, 201


class AuditScoreGetPutDelete(AuthenticatedService):

    def __init__(self):
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
            return {"error": "Override Audit Score with the given ID not found."}, 404

        return AUDIT_ITEM_SCORE_SCHEMA.dump(result.__dict__).data, 200

    @admin_permission.require(http_exception=403)
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

        if not result:
            return {"error": "Override Audit Score with the given ID not found."}, 404

        db.session.delete(result)
        db.session.commit()

        return {'status': 'deleted'}, 202


api.add_resource(AuditScoresGet, '/auditscores')
api.add_resource(AuditScoreGetPutDelete, '/auditscores/<int:id>')
