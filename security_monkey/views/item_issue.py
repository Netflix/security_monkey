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

from security_monkey import rbac

from security_monkey.views import AuthenticatedService
from security_monkey.views import ITEM_FIELDS
from security_monkey.views import AUDIT_FIELDS
from security_monkey.views import ITEM_LINK_FIELDS
from security_monkey.datastore import ItemAudit
from security_monkey.datastore import Item
from security_monkey.datastore import Account
from security_monkey.datastore import AccountType
from security_monkey.datastore import Technology
from security_monkey.datastore import ItemRevision
from security_monkey.datastore import AuditorSettings
from security_monkey import AWS_DEFAULT_REGION

from flask_restful import marshal

from sqlalchemy import or_


class ItemAuditList(AuthenticatedService):
    decorators = [
        rbac.allow(["View"], ["GET"])
    ]

    def get(self):
        """
             .. http:get:: /api/1/issues

             Get a list of Audit Issues matching the given criteria

             **Example Request**:

             .. sourcecode:: http

                 GET /api/1/issues HTTP/1.1
                 Host: example.com
                 Accept: application/json, text/javascript

             **Example Response**:

             .. sourcecode:: http

                 HTTP/1.1 200 OK
                 Vary: Accept
                 Content-Type: application/json

                 {
                    items: [
                        {
                            account: "example_account",
                            account_type: "AWS",
                            justification: null,
                            name: "example_name",
                            technology: "s3",
                            issue: "Example Issue",
                            region: AWS_DEFAULT_REGION,
                            score: 10,
                            notes: "Example Notes",
                            item_id: 11,
                            justified: false,
                            justified_date: null,
                            id: 595
                        }
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

        self.reqparse.add_argument('count', type=int, default=30, location='args')
        self.reqparse.add_argument('page', type=int, default=1, location='args')
        self.reqparse.add_argument('regions', type=str, default=None, location='args')
        self.reqparse.add_argument('accounts', type=str, default=None, location='args')
        self.reqparse.add_argument('accounttypes', type=str, default=None, location='args')
        self.reqparse.add_argument('technologies', type=str, default=None, location='args')
        self.reqparse.add_argument('names', type=str, default=None, location='args')
        self.reqparse.add_argument('arns', type=str, default=None, location='args')
        self.reqparse.add_argument('active', type=str, default=None, location='args')
        self.reqparse.add_argument('searchconfig', type=str, default=None, location='args')
        self.reqparse.add_argument('enabledonly', type=bool, default=None, location='args')
        self.reqparse.add_argument('justified', type=str, default=None, location='args')
        self.reqparse.add_argument('summary', type=str, default=None, location='args')
        args = self.reqparse.parse_args()

        page = args.pop('page', None)
        count = args.pop('count', None)
        for k, v in list(args.items()):
            if not v:
                del args[k]

        query = ItemAudit.query.join("item")
        query = query.filter(ItemAudit.fixed == False)
        if 'regions' in args:
            regions = args['regions'].split(',')
            query = query.filter(Item.region.in_(regions))
        if 'accounts' in args:
            accounts = args['accounts'].split(',')
            query = query.join((Account, Account.id == Item.account_id))
            query = query.filter(Account.name.in_(accounts))
        if 'accounttypes' in args:
            accounttypes = args['accounttypes'].split(',')
            query = query.join((Account, Account.id == Item.account_id))
            query = query.join((AccountType, AccountType.id == Account.account_type_id))
            query = query.filter(AccountType.name.in_(accounttypes))
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
        if 'active' in args:
            active = args['active'].lower() == "true"
            query = query.join((ItemRevision, Item.latest_revision_id == ItemRevision.id))
            query = query.filter(ItemRevision.active == active)
        if 'searchconfig' in args:
            search = args['searchconfig'].split(',')
            conditions = []
            for searchterm in search:
                conditions.append(ItemAudit.issue.ilike('%{}%'.format(searchterm)))
                conditions.append(ItemAudit.notes.ilike('%{}%'.format(searchterm)))
                conditions.append(ItemAudit.justification.ilike('%{}%'.format(searchterm)))
                conditions.append(Item.name.ilike('%{}%'.format(searchterm))) 
            query = query.filter(or_(*conditions))
        if 'enabledonly' in args:
            query = query.join((AuditorSettings, AuditorSettings.id == ItemAudit.auditor_setting_id))
            query = query.filter(AuditorSettings.disabled == False)
        if 'justified' in args:
            justified = args['justified'].lower() == "true"
            query = query.filter(ItemAudit.justified == justified)
        if 'summary' in args:
            # Summary wants to order by oldest issues
            # TODO: Add date_created column to ItemAudit, and have summary order by date_created
            # Order by justified_date until date_created exists
            query = query.order_by(ItemAudit.justified_date.asc())
        else:
            query = query.order_by(ItemAudit.justified, ItemAudit.score.desc())

        issues = query.paginate(page, count)

        marshaled_dict = {
            'page': issues.page,
            'total': issues.total,
            'auth': self.auth_dict
        }

        items_marshaled = []
        for issue in issues.items:
            # TODO: This MUST be modified when switching to new issue logic in future:
            #       Currently there should be exactly 1 item in the list of sub_items:
            item_marshaled = marshal(issue.item.__dict__, ITEM_FIELDS)
            issue_marshaled = marshal(issue.__dict__, AUDIT_FIELDS)
            account_marshaled = {'account': issue.item.account.name}
            accounttype_marshaled = {'account_type': issue.item.account.account_type.name}
            technology_marshaled = {'technology': issue.item.technology.name}

            links = []
            for link in issue.sub_items:
                item_link_marshaled = marshal(link.__dict__, ITEM_LINK_FIELDS)
                links.append(item_link_marshaled)

            issue_marshaled['item_links'] = links

            if issue.justified:
                if issue.user is not None:
                    issue_marshaled = dict(
                        list(issue_marshaled.items()) +
                        list({'justified_user': issue.user.email}.items()))
            merged_marshaled = dict(
                list(item_marshaled.items()) +
                list(issue_marshaled.items()) +
                list(account_marshaled.items()) +
                list(accounttype_marshaled.items()) +
                list(technology_marshaled.items()))
            items_marshaled.append(merged_marshaled)

        marshaled_dict['items'] = items_marshaled
        marshaled_dict['count'] = len(items_marshaled)
        return marshaled_dict, 200


class ItemAuditGet(AuthenticatedService):
    decorators = [
        rbac.allow(["View"], ["GET"])
    ]

    def get(self, audit_id):
        """
            .. http:get:: /api/1/issue/1234

            Get a specific issue

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/issue/1234 HTTP/1.1
                Host: example.com
                Accept: application/json

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    justification: null,
                    name: "example_name",
                    issue: "Example Audit Issue",
                    notes: "Example Notes on Audit Issue",
                    auth: {
                        authenticated: true,
                        user: "user@example.com"
                    },
                    score: 0,
                    item_id: 704,
                    region: AWS_DEFAULT_REGION,
                    justified: false,
                    justified_date: null,
                    id: 704
                }

            :statuscode 200: no error
            :statuscode 401: Authentication Error. Please login.
        """

        query = ItemAudit.query.join("item").filter(ItemAudit.id == audit_id)
        result = query.first()

        issue_marshaled = marshal(result, AUDIT_FIELDS)
        item_marshaled = marshal(result.item, ITEM_FIELDS)
        issue_marshaled = dict(
            list(issue_marshaled.items()) +
            list(item_marshaled.items()) +
            list({'auth': self.auth_dict}.items())
        )
        return issue_marshaled, 200
