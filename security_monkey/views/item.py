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
from security_monkey.views import ITEM_FIELDS
from security_monkey.views import ITEM_COMMENT_FIELDS
from security_monkey.views import AUDIT_FIELDS
from security_monkey.views import REVISION_FIELDS
from security_monkey.datastore import Item
from security_monkey.datastore import Account
from security_monkey.datastore import Technology
from security_monkey.datastore import ItemRevision
from security_monkey import db
from security_monkey import api

from flask.ext.restful import marshal, reqparse
from sqlalchemy.sql.expression import cast
from sqlalchemy import String


class ItemGet(AuthenticatedService):
    def __init__(self):
        super(ItemGet, self).__init__()

    def get(self, item_id):
        """
            .. http:get:: /api/1/item/1234

            Get a specific item

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/item/1234 HTTP/1.1
                Host: example.com
                Accept: application/json

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "item": {
                        "account": "example_account",
                        "region": "us-east-1",
                        "technology": "elb",
                        "id": 1234,
                        "name": "example_name"
                    },
                    "revisions": [
                        {
                            "active": false,
                            "date_created": "2014-04-11 17:05:06.701936",
                            "config": {},
                            "item_id": 1234,
                            "id": 213784
                        }                    ],
                    "auth": {
                        "authenticated": true,
                        "user": "user@example.com"
                    },
                    "issues": [],
                    "comments": []
                }

            :statuscode 200: no error
            :statuscode 401: Authenticaiton Error Please login.
        """

        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        query = Item.query.filter(Item.id == item_id)
        result = query.first()

        # result should be an Item with a list of audit thingers and a list of
        # revisions
        retval = {}

        item_marshaled = marshal(result.__dict__, ITEM_FIELDS)
        item_marshaled = dict(
            item_marshaled.items() +
            {'account': result.account.name}.items() +
            {'technology': result.technology.name}.items()
        )
        retval['item'] = item_marshaled
        retval['issues'] = []
        retval['auth'] = self.auth_dict

        comments_marshaled = []
        for comment in result.comments:
            comment_marshaled = marshal(comment, ITEM_COMMENT_FIELDS)
            comment_marshaled = dict(
                comment_marshaled.items() +
                {'user': comment.user.email}.items()
            )
            comments_marshaled.append(comment_marshaled)
        retval['comments'] = comments_marshaled

        for issue in result.issues:
            issue_marshaled = marshal(issue.__dict__, AUDIT_FIELDS)
            if issue.user is not None:
                issue_marshaled = dict(issue_marshaled.items() +
                                       {'justified_user': issue.user.email}.items()
                                       )
            retval['issues'].append(issue_marshaled)

        retval['revisions'] = []
        for revision in result.revisions:
            revision_marshaled = marshal(revision.__dict__, REVISION_FIELDS)
            revision_marshaled = dict(
                revision_marshaled.items() +
                {'config': revision.config}.items()
            )
            retval['revisions'].append(revision_marshaled)

        return retval, 200


# Returns a list of items optionally filtered by
#  account, region, name, ctype or id.
class ItemList(AuthenticatedService):
    def __init__(self):
        super(ItemList, self).__init__()

    def get(self):
        """
            .. http:get:: /api/1/items

            Get a list of items matching the given criteria.

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/items HTTP/1.1
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
                            "region": "us-east-1",
                            "technology": "sqs",
                            "id": 14414,
                            "name": "example_name",
                            "num_issues": 3,
                            "issue_score": 9,
                            "unjustified_issue_score": 3,
                            "active" true,
                            "first_seen": "2014-06-17 19:47:07.299760",
                            "last_seen": "2014-06-18 11:53:16.467709"
                        }
                    ],
                    "total": 144,
                    "page": 1,
                    "auth": {
                        "authenticated": true,
                        "user": "user@example.com"
                    }
                }

            :statuscode 200: no error
            :statuscode 401: Authenciation Error. Please Login.
        """

        (auth, retval) = __check_auth__(self.auth_dict)
        if auth:
            return retval

        self.reqparse.add_argument('count', type=int, default=30, location='args')
        self.reqparse.add_argument('page', type=int, default=1, location='args')
        self.reqparse.add_argument('regions', type=str, default=None, location='args')
        self.reqparse.add_argument('accounts', type=str, default=None, location='args')
        self.reqparse.add_argument('active', type=str, default=None, location='args')
        self.reqparse.add_argument('names', type=str, default=None, location='args')
        self.reqparse.add_argument('technologies', type=str, default=None, location='args')
        self.reqparse.add_argument('searchconfig', type=str, default=None, location='args')
        self.reqparse.add_argument('ids', type=int, default=None, location='args')
        args = self.reqparse.parse_args()

        page = args.pop('page', None)
        count = args.pop('count', None)
        for k, v in args.items():
            if not v:
                del args[k]

        # Read more about filtering:
        # http://docs.sqlalchemy.org/en/rel_0_7/orm/query.html
        query = Item.query.join((ItemRevision, Item.latest_revision_id == ItemRevision.id))
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
        if 'ids' in args:
            ids = args['ids'].split(',')
            query = query.filter(Item.id.in_(ids))
        if 'active' in args:
            active = args['active'].lower() == "true"
            query = query.filter(ItemRevision.active == active)
        if 'searchconfig' in args:
            searchconfig = args['searchconfig']
            query = query.filter(cast(ItemRevision.config, String).ilike('%{}%'.format(searchconfig)))

        query = query.order_by(ItemRevision.date_created.desc())

        items = query.paginate(page, count)

        marshaled_dict = {
            'page': items.page,
            'total': items.total,
            'auth': self.auth_dict
        }

        marshaled_items = []
        for item in items.items:
            num_issues = len(item.issues)

            issue_score = 0
            unjustified_issue_score = 0
            for issue in item.issues:
                issue_score = issue_score + issue.score

                if not issue.justified:
                    unjustified_issue_score += issue.score

            first_seen = str(item.revisions[-1].date_created)
            last_seen = str(item.revisions[0].date_created)
            active = item.revisions[0].active

            item_marshaled = {}
            item_marshaled = marshal(item.__dict__, ITEM_FIELDS)
            item_marshaled = dict(item_marshaled.items() +
                                  {
                                      'account': item.account.name,
                                      'technology': item.technology.name,
                                      'num_issues': num_issues,
                                      'issue_score': issue_score,
                                      'unjustified_issue_score': unjustified_issue_score,
                                      'active': active,
                                      'first_seen': first_seen,
                                      'last_seen': last_seen
                                      #'last_rev': item.revisions[0].config,
                                  }.items())

            marshaled_items.append(item_marshaled)

        marshaled_dict['items'] = marshaled_items
        marshaled_dict['count'] = len(marshaled_items)

        return marshaled_dict, 200
