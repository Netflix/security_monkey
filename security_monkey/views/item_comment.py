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

from six import text_type

from security_monkey.views import AuthenticatedService
from security_monkey.views import ITEM_COMMENT_FIELDS
from security_monkey.datastore import ItemComment
from security_monkey import db, rbac

from flask_restful import marshal
from flask_login import current_user
import datetime


class ItemCommentDelete(AuthenticatedService):
    decorators = [
        rbac.allow(['Justify'], ["DELETE"])
    ]

    def delete(self, item_id, comment_id):
        """
            .. http:delete:: /api/1/items/<int:item_id>/comment/<int:comment_id>

            Deletes an item comment.

            **Example Request**:

            .. sourcecode:: http

                DELETE /api/1/items/1234/comment/7718 HTTP/1.1
                Host: example.com
                Accept: application/json

                {
                }

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 202 OK
                Vary: Accept
                Content-Type: application/json

                {
                    'status': 'deleted'
                }

            :statuscode 202: Deleted
            :statuscode 401: Authentication Error. Please Login.
        """

        query = ItemComment.query.filter(ItemComment.id == comment_id)
        query.filter(ItemComment.user_id == current_user.id).delete()
        db.session.commit()

        return {'result': 'success'}, 202


class ItemCommentGet(AuthenticatedService):
    decorators = [rbac.allow(['View'], ["GET"])]

    def get(self, item_id, comment_id):
        """
            .. http:get:: /api/1/items/<int:item_id>/comment/<int:comment_id>

            Retrieves an item comment.

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/items/1234/comment/7718 HTTP/1.1
                Host: example.com
                Accept: application/json

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    'id': 7719,
                    'date_created': "2013-10-04 22:01:47",
                    'text': 'This is an Item Comment.',
                    'item_id': 1111
                }

            :statuscode 200: Success
            :statuscode 404: Comment with given ID not found.
            :statuscode 401: Authentication Error. Please Login.
        """

        query = ItemComment.query.filter(ItemComment.id == comment_id)
        query = query.filter(ItemComment.item_id == item_id)
        ic = query.first()

        if ic is None:
            return {"status": "Item Comment Not Found"}, 404

        comment_marshaled = marshal(ic.__dict__, ITEM_COMMENT_FIELDS)
        comment_marshaled = dict(
            list(comment_marshaled.items()) +
            list({'user': ic.user.email}.items())
        )

        return comment_marshaled, 200


class ItemCommentPost(AuthenticatedService):
    decorators = [
        rbac.allow(['Comment'], ["POST"])
    ]

    def post(self, item_id):
        """
            .. http:post:: /api/1/items/<int:item_id>/comments

            Adds an item comment.

            **Example Request**:

            .. sourcecode:: http

                POST /api/1/items/1234/comments HTTP/1.1
                Host: example.com
                Accept: application/json

                {
                    "text": "This item is my favorite."
                }

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 201 OK
                Vary: Accept
                Content-Type: application/json

                {
                    'item_id': 1234,
                    'id': 7718,
                    'comment': 'This item is my favorite.',
                    'user': 'user@example.com'
                }
                {
                    "date_created": "2014-10-11 23:03:47.716698",
                    "id": 1,
                    "text": "This is an item comment."
                }

            :statuscode 201: Created
            :statuscode 401: Authentication Error. Please Login.
        """

        self.reqparse.add_argument('text', required=False, type=text_type, help='Must provide comment', location='json')
        args = self.reqparse.parse_args()

        ic = ItemComment()
        ic.user_id = current_user.id
        ic.item_id = item_id
        ic.text = args['text']
        ic.date_created = datetime.datetime.utcnow()

        db.session.add(ic)
        db.session.commit()
        db.session.refresh(ic)

        comment_marshaled = marshal(ic.__dict__, ITEM_COMMENT_FIELDS)
        comment_marshaled = dict(
            list(comment_marshaled.items()) +
            list({'user': ic.user.email}.items())
        )

        return comment_marshaled, 201
