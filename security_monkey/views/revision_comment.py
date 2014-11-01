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
from security_monkey.views import REVISION_COMMENT_FIELDS
from security_monkey.datastore import ItemRevisionComment
from security_monkey import db
from security_monkey import api

from flask.ext.restful import marshal, reqparse
from flask.ext.login import current_user
import datetime


class RevisionCommentGet(AuthenticatedService):
    def __init__(self):
        super(RevisionCommentGet, self).__init__()

    def get(self, revision_id, comment_id):
        """
            .. http:get:: /api/1/revisions/<int:revision_id>/comments/<int:comment_id>

            Get a specific Revision Comment

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/revisions/1141/comments/22 HTTP/1.1
                Host: example.com
                Accept: application/json


            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    'id': 22,
                    'revision_id': 1141,
                    "date_created": "2013-10-04 22:01:47",
                    'text': 'This is a Revision Comment.'
                }

            :statuscode 200: no error
            :statuscode 404: Revision Comment with given ID not found.
            :statuscode 401: Authentication Error. Please Login.
        """

        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        query = ItemRevisionComment.query.filter(ItemRevisionComment.id == comment_id)
        query = query.filter(ItemRevisionComment.revision_id == revision_id)
        irc = query.first()

        if irc is None:
            return {"status": "Revision Comment Not Found"}, 404

        revision_marshaled = marshal(irc.__dict__, REVISION_COMMENT_FIELDS)
        revision_marshaled = dict(
            revision_marshaled.items() +
            {'user': irc.user.email}.items()
        )

        return revision_marshaled, 200


class RevisionCommentDelete(AuthenticatedService):
    def __init__(self):
        super(RevisionCommentDelete, self).__init__()

    def delete(self, revision_id, comment_id):
        """
            .. http:delete:: /api/1/revisions/<int:revision_id>/comments/<int:comment_id>

            Delete a specific Revision Comment

            **Example Request**:

            .. sourcecode:: http

                DELETE /api/1/revisions/1141/comments/22 HTTP/1.1
                Host: example.com
                Accept: application/json


            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    'status': "deleted"
                }

            :statuscode 202: Comment Deleted
            :statuscode 404: Revision Comment with given ID not found.
            :statuscode 401: Authentication Error. Please Login.
        """

        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        query = ItemRevisionComment.query.filter(ItemRevisionComment.id == comment_id)
        query = query.filter(ItemRevisionComment.revision_id == revision_id)
        irc = query.first()

        if irc is None:
            return {"status": "Revision Comment Not Found"}, 404

        query.delete()
        db.session.commit()

        return {"status": "deleted"}, 202


class RevisionCommentPost(AuthenticatedService):
    def __init__(self):
        super(RevisionCommentPost, self).__init__()

    def post(self, revision_id):
        """
            .. http:post:: /api/1/revisions/<int:revision_id>/comments

            Create a new Revision Comment.

            **Example Request**:

            .. sourcecode:: http

                POST /api/1/revisions/1141/comments HTTP/1.1
                Host: example.com
                Accept: application/json

                {
                    "text": "This is a Revision Comment."
                }


            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 201 OK
                Vary: Accept
                Content-Type: application/json

                {
                    'id': 22,
                    'revision_id': 1141,
                    "date_created": "2013-10-04 22:01:47",
                    'text': 'This is a Revision Comment.'
                }

            :statuscode 201: Revision Comment Created
            :statuscode 401: Authentication Error. Please Login.
        """

        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        self.reqparse.add_argument('text', required=False, type=unicode, help='Must provide comment', location='json')
        args = self.reqparse.parse_args()

        irc = ItemRevisionComment()
        irc.user_id = current_user.id
        irc.revision_id = revision_id
        irc.text = args['text']
        irc.date_created = datetime.datetime.utcnow()
        db.session.add(irc)
        db.session.commit()

        irc_committed = ItemRevisionComment.query.filter(ItemRevisionComment.id == irc.id).first()
        revision_marshaled = marshal(irc_committed.__dict__, REVISION_COMMENT_FIELDS)
        revision_marshaled = dict(
            revision_marshaled.items() +
            {'user': irc_committed.user.email}.items()
        )
        return revision_marshaled, 200
