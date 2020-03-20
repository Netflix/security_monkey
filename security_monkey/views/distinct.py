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
from security_monkey.datastore import Item
from security_monkey.datastore import Account
from security_monkey.datastore import AccountType
from security_monkey.datastore import Technology
from security_monkey.datastore import ItemRevision
from security_monkey import rbac

from flask_restful import reqparse
from sqlalchemy.sql.expression import func

import json


class Distinct(AuthenticatedService):
    decorators = [
        rbac.allow(["View"], ["GET"])
    ]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(Distinct, self).__init__()

    def get(self, key_id):
        """
            .. http:get:: /api/1/distinct

            Get a list of distinct regions, names, accounts, accounttypes or technologies

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/distinct/name HTTP/1.1
                Host: example.com
                Accept: application/json, text/javascript

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

            :statuscode 200: no error
        """

        self.reqparse.add_argument('count', type=int, default=30, location='args')
        self.reqparse.add_argument('page', type=int, default=1, location='args')
        self.reqparse.add_argument('select2', type=str, default="", location='args')
        self.reqparse.add_argument('searchconfig', type=str, default="", location='args')

        self.reqparse.add_argument('regions', type=str, default=None, location='args')
        self.reqparse.add_argument('accounts', type=str, default=None, location='args')
        self.reqparse.add_argument('accounttypes', type=str, default=None, location='args')
        self.reqparse.add_argument('technologies', type=str, default=None, location='args')
        self.reqparse.add_argument('names', type=str, default=None, location='args')
        self.reqparse.add_argument('active', type=str, default=None, location='args')

        args = self.reqparse.parse_args()
        page = args.pop('page', None)
        count = args.pop('count', None)
        q = args.pop('searchconfig', "").lower()
        select2 = args.pop('select2', "")
        for k, v in list(args.items()):
            if not v:
                del args[k]

        if select2.lower() == 'true':
            select2 = True
        else:
            select2 = False

        query = Item.query
        if 'regions' in args and key_id != 'region':
            regions = args['regions'].split(',')
            query = query.filter(Item.region.in_(regions))
        if 'accounts' in args and key_id != 'account':
            query = query.join((Account, Account.id == Item.account_id))
            accounts = args['accounts'].split(',')
            query = query.filter(Account.name.in_(accounts))
        if 'accounttypes' in args and key_id != 'accounttype':
            query = query.join((Account, Account.id == Item.account_id)).join(
                (AccountType, AccountType.id == Account.account_type_id))
            accounttypes = args['accounttypes'].split(',')
            query = query.filter(AccountType.name.in_(accounttypes))
        if 'technologies' in args and key_id != 'tech':
            query = query.join((Technology, Technology.id == Item.tech_id))
            technologies = args['technologies'].split(',')
            query = query.filter(Technology.name.in_(technologies))
        if 'names' in args and key_id != 'name':
            names = args['names'].split(',')
            query = query.filter(Item.name.in_(names))
        if 'arns' in args and key_id != 'arn':
            names = args['arns'].split(',')
            query = query.filter(Item.arn.in_(names))
        if 'active' in args:
            query = query.join((ItemRevision, Item.latest_revision_id == ItemRevision.id))
            active = args['active'].lower() == "true"
            query = query.filter(ItemRevision.active == active)

        if key_id == 'tech':
            query = query.join((Technology, Technology.id == Item.tech_id))
            if select2:
                query = query.distinct(Technology.name).filter(func.lower(Technology.name).like('%' + q + '%'))
            else:
                query = query.distinct(Technology.name)
        elif key_id == 'accounttype':
            query = query.join((Account, Account.id == Item.account_id)).join(
                (AccountType, AccountType.id == Account.account_type_id))
            if select2:
                query = query.distinct(AccountType.name).filter(func.lower(AccountType.name).like('%' + q + '%'))
            else:
                query = query.distinct(AccountType.name)
        elif key_id == 'account':
            query = query.join((Account, Account.id == Item.account_id))
            if select2:
                query = query.filter(Account.third_party == False)
                query = query.distinct(Account.name).filter(func.lower(Account.name).like('%' + q + '%'))
            else:
                query = query.distinct(Account.name)

        else:
            filter_by = None
            if key_id == "region":
                filter_by = Item.region
            elif key_id == "name":
                filter_by = Item.name
            elif key_id == "arn":
                filter_by = Item.arn
            else:
                return json.loads('{ "error": "Supply key in type,region,account,name,arn" }')

            if select2:
                query = query.distinct(filter_by).filter(func.lower(filter_by).like('%' + q + '%'))
            else:
                query = query.distinct(filter_by)

        items = query.paginate(page, count, error_out=False)

        marshaled_dict = {}
        list_distinct = []
        for item in items.items:
            if key_id == "tech":
                text = item.technology.name
                item_id = item.id
            elif key_id == "account":
                text = item.account.name
                item_id = item.id
            elif key_id == "accounttype":
                text = item.account.account_type.name
                item_id = item.id
            elif key_id == "region":
                text = item.region
                item_id = item.id
            elif key_id == "name":
                text = item.name
                item_id = item.id
            elif key_id == "arn":
                text = item.arn
                item_id = item.id
            if(select2):
                list_distinct.append({"id": item_id, "text": text})
            else:
                list_distinct.append(text)

        marshaled_dict['auth'] = self.auth_dict
        marshaled_dict['items'] = list_distinct
        marshaled_dict['page'] = items.page
        marshaled_dict['total'] = items.total
        marshaled_dict['key_id'] = key_id
        return marshaled_dict, 200
