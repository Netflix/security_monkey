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

from security_monkey.common.utils.PolicyDiff import PolicyDiff
from security_monkey.views import AuthenticatedService
from security_monkey.views import __check_auth__
from security_monkey.views import REVISION_FIELDS
from security_monkey.views import REVISION_COMMENT_FIELDS
from security_monkey.views import ITEM_FIELDS
from security_monkey.datastore import Item
from security_monkey.datastore import Account
from security_monkey.datastore import Technology
from security_monkey.datastore import ItemRevision
from security_monkey import db
from security_monkey import api

from flask.ext.restful import marshal, reqparse


class RevisionGet(AuthenticatedService):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(RevisionGet, self).__init__()

    def get(self, revision_id):
        """
            .. http:get:: /api/1/revision/1234

            Get a specific revision.

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/revision/123 HTTP/1.1
                Host: example.com
                Accept: application/json, text/javascript

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
                    "item_id": 114,
                    "comments": [],
                    "active": false,
                    "date_created": "2013-10-04 22:01:47",
                    "config": {},
                    "id":123
                }

            :statuscode 200: no error
            :statuscode 401: Authentication failure. Please login.
        """
        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        query = ItemRevision.query.filter(ItemRevision.id == revision_id)
        result = query.first()

        comments = []
        for comment in result.comments:
            comment_marshaled = marshal(comment, REVISION_COMMENT_FIELDS)
            comments.append(dict(
                comment_marshaled.items() +
                {'user': comment.user.email}.items()
            ))

        revision_marshaled = marshal(result, REVISION_FIELDS)
        revision_marshaled = dict(
            revision_marshaled.items() +
            {'config': result.config}.items() +
            {'auth': self.auth_dict}.items() +
            {'comments': comments}.items()

        )

        self.reqparse.add_argument('compare', type=int, default=None, location='args')
        args = self.reqparse.parse_args()
        compare_id = args.pop('compare', None)
        print "compare_id {}".format(compare_id)
        if compare_id:
            query = ItemRevision.query.filter(ItemRevision.id == compare_id)
            compare_result = query.first()
            pdiff = PolicyDiff(result.config, compare_result.config)
            revision_marshaled = dict(
                revision_marshaled.items() +
                {'diff_html': pdiff.produceDiffHTML()}.items()
            )

        return revision_marshaled, 200


class RevisionList(AuthenticatedService):
    def __init__(self):
        super(RevisionList, self).__init__()

    def get(self):
        """
            .. http:get:: /api/1/revisions

            Get a list of revisions

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/revisions?count=1 HTTP/1.1
                Host: example.com
                Accept: application/json

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "items": [
                        {
                            "account": "example_account",
                            "name": "Example Name",
                            "region": "us-east-1",
                            "item_id": 144,
                            "active": false,
                            "date_created": "2014-06-19 20:54:12.962951",
                            "technology": "sqs",
                            "id": 223757
                        }
                    ],
                    "total": 1,
                    "page": 1,
                    "auth": {
                        "authenticated": true,
                        "user": "user@example.com"
                    }
                }

            :statuscode 200: no error
            :statuscode 401: Authentication Error. Please Login.
        """

        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        self.reqparse.add_argument('count', type=int, default=30, location='args')
        self.reqparse.add_argument('page', type=int, default=1, location='args')
        self.reqparse.add_argument('active', type=str, default=None, location='args')
        self.reqparse.add_argument('regions', type=str, default=None, location='args')
        self.reqparse.add_argument('accounts', type=str, default=None, location='args')
        self.reqparse.add_argument('names', type=str, default=None, location='args')
        self.reqparse.add_argument('technologies', type=str, default=None, location='args')
        self.reqparse.add_argument('searchconfig', type=str, default=None, location='args')
        args = self.reqparse.parse_args()

        page = args.pop('page', None)
        count = args.pop('count', None)
        for k, v in args.items():
            if not v:
                del args[k]

        query = ItemRevision.query.join("item")
        if 'regions' in args:
            regions = args['regions'].split(',')
            query = query.filter(Item.region.in_(regions))
        if 'accounts' in args:
            accounts = args['accounts'].split(',')
            query = query.join((Account, Account.id == Item.account_id))
            query = query.filter(Account.name.in_(accounts))
        if 'technologies' in args:
            technologies = args['technologies'].split(',')
            query = query.join((Technology, Technology.id == Item.tech_id))
            query = query.filter(Technology.name.in_(technologies))
        if 'names' in args:
            names = args['names'].split(',')
            query = query.filter(Item.name.in_(names))
        if 'active' in args:
            active = args['active'].lower() == "true"
            query = query.filter(ItemRevision.active == active)
        if 'searchconfig' in args:
            searchconfig = args['searchconfig']
            query = query.filter(cast(ItemRevision.config, String).ilike('%{}%'.format(searchconfig)))
        query = query.order_by(ItemRevision.date_created.desc())
        revisions = query.paginate(page, count)

        marshaled_dict = {}
        marshaled_dict['page'] = revisions.page
        marshaled_dict['total'] = revisions.total
        marshaled_dict['auth'] = self.auth_dict

        items_marshaled = []
        for revision in revisions.items:
            item_marshaled = marshal(revision.item.__dict__, ITEM_FIELDS)
            revision_marshaled = marshal(revision.__dict__, REVISION_FIELDS)
            account_marshaled = {'account': revision.item.account.name}
            technology_marshaled = {'technology': revision.item.technology.name}
            merged_marshaled = dict(
                item_marshaled.items() +
                revision_marshaled.items() +
                account_marshaled.items() +
                technology_marshaled.items())
            items_marshaled.append(merged_marshaled)

        marshaled_dict['items'] = items_marshaled
        marshaled_dict['count'] = len(items_marshaled)
        return marshaled_dict, 200
