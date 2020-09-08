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
from security_monkey.views import ITEM_FIELDS
from security_monkey.views import ITEM_COMMENT_FIELDS
from security_monkey.views import AUDIT_FIELDS
from security_monkey.views import REVISION_FIELDS
from security_monkey.views import ITEM_LINK_FIELDS
from security_monkey.datastore import Item
from security_monkey.datastore import Account
from security_monkey.datastore import AccountType
from security_monkey.datastore import Technology
from security_monkey.datastore import ItemRevision
from security_monkey import rbac, AWS_DEFAULT_REGION

from flask_restful import marshal, reqparse
from sqlalchemy.sql.expression import cast
from sqlalchemy import String
from sqlalchemy.orm import joinedload


class ItemGet(AuthenticatedService):
    decorators = [rbac.allow(['View'], ["GET"])]

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
                        "region": AWS_DEFAULT_REGION,
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

        query = Item.query.filter(Item.id == item_id)
        result = query.first()

        # result should be an Item with a list of audit thingers and a list of
        # revisions
        retval = {}

        item_marshaled = marshal(result.__dict__, ITEM_FIELDS)
        item_marshaled = dict(
            list(item_marshaled.items()) +
            list({'account': result.account.name}.items()) +
            list({'account_type': result.account.account_type.name}.items()) +
            list({'technology': result.technology.name}.items())
        )
        retval['item'] = item_marshaled
        retval['issues'] = []
        retval['auth'] = self.auth_dict

        comments_marshaled = []
        for comment in result.comments:
            comment_marshaled = marshal(comment, ITEM_COMMENT_FIELDS)
            comment_marshaled = dict(
                list(comment_marshaled.items()) +
                list({'user': comment.user.email}.items())
            )
            comments_marshaled.append(comment_marshaled)
        retval['comments'] = comments_marshaled

        for issue in result.issues:
            if not issue.auditor_setting or issue.auditor_setting.disabled:
                continue
            issue_marshaled = marshal(issue.__dict__, AUDIT_FIELDS)
            if issue.user is not None:
                issue_marshaled = dict(list(issue_marshaled.items()) +
                                       list({'justified_user': issue.user.email}.items())
                                       )

            links = []
            for link in issue.sub_items:
                item_link_marshaled = marshal(link.__dict__, ITEM_LINK_FIELDS)
                links.append(item_link_marshaled)

            issue_marshaled['item_links'] = links

            retval['issues'].append(issue_marshaled)

        retval['revisions'] = []
        for revision in result.revisions.all():
            revision_marshaled = marshal(revision.__dict__, REVISION_FIELDS)
            retval['revisions'].append(revision_marshaled)

        return retval, 200


# Returns a list of items optionally filtered by
#  account, account_type, region, name, ctype or id.
class ItemList(AuthenticatedService):
    decorators = [rbac.allow(['View'], ["GET"])]

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
                            "account_type": "AWS",
                            "region": AWS_DEFAULT_REGION,
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

        self.reqparse.add_argument('count', type=int, default=30, location='args')
        self.reqparse.add_argument('page', type=int, default=1, location='args')
        self.reqparse.add_argument('regions', type=str, default=None, location='args')
        self.reqparse.add_argument('accounts', type=str, default=None, location='args')
        self.reqparse.add_argument('accounttypes', type=str, default=None, location='args')
        self.reqparse.add_argument('active', type=str, default=None, location='args')
        self.reqparse.add_argument('names', type=str, default=None, location='args')
        self.reqparse.add_argument('arns', type=str, default=None, location='args')
        self.reqparse.add_argument('technologies', type=str, default=None, location='args')
        self.reqparse.add_argument('searchconfig', type=str, default=None, location='args')
        self.reqparse.add_argument('ids', type=int, default=None, location='args')
        self.reqparse.add_argument('summary', type=bool, default=False, location='args')
        self.reqparse.add_argument('min_score', type=int, default=False, location='args')
        self.reqparse.add_argument('min_unjustified_score', type=int, default=False, location='args')
        args = self.reqparse.parse_args()

        page = args.pop('page', None)
        count = args.pop('count', None)
        for k, v in list(args.items()):
            if not v:
                del args[k]

        # Read more about filtering:
        # https://docs.sqlalchemy.org/en/latest/orm/query.html
        query = Item.query.join((ItemRevision, Item.latest_revision_id == ItemRevision.id))
        
        # Fix for issue https://github.com/Netflix/security_monkey/issues/1150
        # PR https://github.com/Netflix/security_monkey/pull/1153
        join_account = False
        
        if 'regions' in args:
            regions = args['regions'].split(',')
            query = query.filter(Item.region.in_(regions))
        if 'accounts' in args:
            accounts = args['accounts'].split(',')
            query = query.filter(Account.name.in_(accounts))
            join_account = True
        if 'accounttypes' in args:
            accounttypes = args['accounttypes'].split(',')
            query = query.join((AccountType, AccountType.id == Account.account_type_id))
            query = query.filter(AccountType.name.in_(accounttypes))
            join_account = True
        if 'technologies' in args:
            technologies = args['technologies'].split(',')
            query = query.join((Technology, Technology.id == Item.tech_id))
            query = query.filter(Technology.name.in_(technologies))
        if 'names' in args:
            names = args['names'].split(',')
            query = query.filter(Item.name.in_(names))
        if 'arns' in args:
            arns = args['arns'].split(',')
            query = query.filter(Item.arn.in_(arns))
        if 'ids' in args:
            ids = args['ids'].split(',')
            query = query.filter(Item.id.in_(ids))
        if 'active' in args:
            active = args['active'].lower() == "true"
            query = query.filter(ItemRevision.active == active)
            query = query.filter(Account.active == True)
            join_account = True
        if 'searchconfig' in args:
            searchconfig = args['searchconfig']
            query = query.filter(cast(ItemRevision.config, String).ilike('%{}%'.format(searchconfig)))
        if 'min_score' in args:
            min_score = args['min_score']
            query = query.filter(Item.score >= min_score)
        if 'min_unjustified_score' in args:
            min_unjustified_score = args['min_unjustified_score']
            query = query.filter(Item.unjustified_score >= min_unjustified_score)
        if join_account == True:
            query = query.join((Account, Account.id == Item.account_id))
 

        # Eager load the joins except for the revisions because of the dynamic lazy relationship
        query = query.options(joinedload('issues'))
        query = query.options(joinedload('account'))
        query = query.options(joinedload('technology'))

        query = query.order_by(ItemRevision.date_created.desc())

        items = query.paginate(page, count)

        marshaled_dict = {
            'page': items.page,
            'total': items.total,
            'auth': self.auth_dict
        }

        marshaled_items = []
        for item in items.items:
            item_marshaled = marshal(item.__dict__, ITEM_FIELDS)

            if 'summary' in args and args['summary']:
                item_marshaled = dict(list(item_marshaled.items()) +
                                      list({
                                          'account': item.account.name,
                                          'account_type': item.account.account_type.name,
                                          'technology': item.technology.name,
                                          'num_issues': item.issue_count,
                                          'issue_score': item.score,
                                          'unjustified_issue_score': item.unjustified_score,
                                          'active': active,
                                          #'last_rev': item.revisions[0].config,
                                      }.items()))
            else:
                first_seen_query = ItemRevision.query.filter(
                    ItemRevision.item_id == item.id
                ).order_by(ItemRevision.date_created.asc())
                first_seen = str(first_seen_query.first().date_created)
                last_seen = str(item.revisions.first().date_created)
                active = item.revisions.first().active
                item_marshaled = dict(list(item_marshaled.items()) +
                                      list({
                                          'account': item.account.name,
                                          'account_type': item.account.account_type.name,
                                          'technology': item.technology.name,
                                          'num_issues': item.issue_count,
                                          'issue_score': item.score,
                                          'unjustified_issue_score': item.unjustified_score,
                                          'active': active,
                                          'first_seen': first_seen,
                                          'last_seen': last_seen
                                          # 'last_rev': item.revisions[0].config,
                                      }.items()))

            marshaled_items.append(item_marshaled)

        marshaled_dict['items'] = marshaled_items
        marshaled_dict['count'] = len(marshaled_items)

        return marshaled_dict, 200
