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
from security_monkey.datastore import Item, ItemRevision, ItemAudit, Account, Technology, User, ItemRevisionComment, ItemComment
from security_monkey import db
from security_monkey.common.utils.PolicyDiff import PolicyDiff

from flask.ext.restful import fields, marshal, Resource, reqparse

from sqlalchemy.sql.expression import func, cast
from sqlalchemy import String

import json
import datetime

# OneLogin and Flask-Login
from security_monkey import app
from flask.ext.login import current_user, logout_user

# CORS
from security_monkey.decorators import crossdomain

ORIGINS = [
    'https://{}:{}'.format(app.config.get('FQDN'), app.config.get('WEB_PORT')),
    # Adding this next one so you can also access the dart UI by prepending /static to the path.
    'https://{}:{}'.format(app.config.get('FQDN'), app.config.get('API_PORT')),
    'https://{}:{}'.format(app.config.get('FQDN'), app.config.get('NGINX_PORT')),
    'https://{}:80'.format(app.config.get('FQDN')),
    # FOR LOCAL DEV IN DART EDITOR:
    'http://127.0.0.1:3030',
    'http://127.0.0.1:8080'
]

# TODO: Delete this when you get a chance.
CORS_HEADERS = {}

##### Marshal Datastructures #####

# Used by RevisionGet, RevisionList, ItemList
REVISION_FIELDS = {
    'id': fields.Integer,
    'date_created': fields.String,
    'active': fields.Boolean,
    'item_id': fields.Integer
}

# Used by RevisionList, ItemGet, ItemList
ITEM_FIELDS = {
    'id': fields.Integer,
    'region': fields.String,
    'name': fields.String
}

# Used by ItemList, Justify
AUDIT_FIELDS = {
    'id': fields.Integer,
    'score': fields.Integer,
    'issue': fields.String,
    'notes': fields.String,
    'justified': fields.Boolean,
    'justification': fields.String,
    'justified_date': fields.String,
    'item_id': fields.Integer
}

## Single Use Marshal Objects ##

# SINGLE USE - RevisionGet
REVISION_COMMENT_FIELDS = {
    'id': fields.Integer,
    'revision_id': fields.Integer,
    'date_created': fields.String,
    'text': fields.String
}

# SINGLE USE - ItemGet
ITEM_COMMENT_FIELDS = {
    'id': fields.Integer,
    'date_created': fields.String,
    'text': fields.String
}

# SINGLE USE - UserSettings
USER_SETTINGS_FIELDS = {
    # 'id': fields.Integer,
    'daily_audit_email': fields.Boolean,
    'change_reports': fields.String
}

# SINGLE USE - AccountGet
ACCOUNT_FIELDS = {
    'id': fields.Integer,
    'name': fields.String,
    's3_name': fields.String,
    'number': fields.String,
    'notes': fields.String,
    'active': fields.Boolean,
    'third_party': fields.Boolean
}


class Logout(Resource):
    def __init__(self):
        super(Logout, self).__init__()

    def get(self):
        if not current_user.is_authenticated():
            return "Must be logged in to log out", 200, CORS_HEADERS
        logout_user()
        return "Logged Out", 200, CORS_HEADERS


class AuthenticatedService(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(AuthenticatedService, self).__init__()
        self.auth_dict = dict()
        if current_user.is_authenticated():
            self.auth_dict = {
                "authenticated": True,
                "user": current_user.email,
            }
        else:
            if app.config.get('FRONTED_BY_NGINX'):
                url = "https://{}:{}{}".format(app.config.get('FQDN'), app.config.get('NGINX_PORT'), '/login')
            else:
                url = "http://{}:{}{}".format(app.config.get('FQDN'), app.config.get('API_PORT'), '/login')
            self.auth_dict = {
                "authenticated": False,
                "user": None,
                "url": url
            }


@app.after_request
@crossdomain(allowed_origins=ORIGINS)
def after(response):
    return response


# Wish I could do this with @app.before_request
def __check_auth__(auth_dict):
    """
    To be called at the beginning of any GET or POST request.
    Returns: True if needs to authenticate.  Also returns the
    JSON containing the SAML url to login.
    Returns None,None when no authentication action needs to occur.
    """
    if not current_user.is_authenticated():
        return True, ({"auth": auth_dict}, 401, CORS_HEADERS)
    return None, None


class Distinct(AuthenticatedService):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(Distinct, self).__init__()

    def get(self, key_id):
        """
            .. http:get:: /api/1/distinct

            Get a list of distinct regions, names, accounts, or technologies

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
        # Disabling Auth on this method because select2 json requests do not support auth.
        # https://github.com/ivaynberg/select2/issues/2450
        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        self.reqparse.add_argument('count', type=int, default=30, location='args')
        self.reqparse.add_argument('page', type=int, default=1, location='args')
        self.reqparse.add_argument('select2', type=str, default="", location='args')
        self.reqparse.add_argument('q', type=str, default="", location='args')

        self.reqparse.add_argument('regions', type=str, default=None, location='args')
        self.reqparse.add_argument('accounts', type=str, default=None, location='args')
        self.reqparse.add_argument('technologies', type=str, default=None, location='args')
        self.reqparse.add_argument('names', type=str, default=None, location='args')
        self.reqparse.add_argument('active', type=str, default=None, location='args')

        args = self.reqparse.parse_args()
        page = args.pop('page', None)
        count = args.pop('count', None)
        q = args.pop('q', "").lower()
        select2 = args.pop('select2', "")
        for k, v in args.items():
            if not v:
                del args[k]

        if select2.lower() == 'true':
            select2 = True
        else:
            select2 = False

        query = Item.query
        query = query.join((Account, Account.id == Item.account_id))
        query = query.join((Technology, Technology.id == Item.tech_id))
        query = query.join((ItemRevision, Item.latest_revision_id == ItemRevision.id))
        if 'regions' in args and key_id != 'region':
            regions = args['regions'].split(',')
            query = query.filter(Item.region.in_(regions))
        if 'accounts' in args and key_id != 'account':
            accounts = args['accounts'].split(',')
            query = query.filter(Account.name.in_(accounts))
        if 'technologies' in args and key_id != 'tech':
            technologies = args['technologies'].split(',')
            query = query.filter(Technology.name.in_(technologies))
        if 'names' in args and key_id != 'name':
            names = args['names'].split(',')
            query = query.filter(Item.name.in_(names))
        if 'active' in args:
            active = args['active'].lower() == "true"
            query = query.filter(ItemRevision.active == active)

        if key_id == 'tech':
            if select2:
                query = query.distinct(Technology.name).filter(func.lower(Technology.name).like('%' + q + '%'))
            else:
                query = query.distinct(Technology.name)
        elif key_id == 'account':
            if select2:
                query = query.filter(Account.third_party==False)
                query = query.distinct(Account.name).filter(func.lower(Account.name).like('%' + q + '%'))
            else:
                query = query.distinct(Account.name)

        else:
            filter_by = None
            if key_id == "region":
                filter_by = Item.region
            elif key_id == "name":
                filter_by = Item.name
            else:
                return json.loads('{ "error": "Supply key in type,region,account,name" }')

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
            elif key_id == "region":
                text = item.region
                item_id = item.id
            elif key_id == "name":
                text = item.name
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
        return marshaled_dict, 200, CORS_HEADERS


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

        return revision_marshaled, 200, CORS_HEADERS


class AccountList(AuthenticatedService):
    def __init__(self):
        super(AccountList, self).__init__()

    def get(self):
        """
            .. http:get:: /api/1/accounts

            Get a list of Accounts matching the given criteria

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/accounts HTTP/1.1
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
                            third_party: false,
                            name: "example_name",
                            notes: null,
                            number: "111111111111",
                            active: true,
                            id: 1,
                            s3_name: "example_name"
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
        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        result = Account.query.order_by(Account.id).all()

        items = []
        for account in result:
            account_marshaled = marshal(account.__dict__, ACCOUNT_FIELDS)
            items.append(account_marshaled)

        marshaled_dict = {}
        marshaled_dict['total'] = len(result)
        marshaled_dict['count'] = len(result)
        marshaled_dict['page'] = 1
        marshaled_dict['items'] = items
        marshaled_dict['auth'] = self.auth_dict
        return marshaled_dict, 200, CORS_HEADERS


class AccountGet(AuthenticatedService):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(AccountGet, self).__init__()

    def get(self, account_id):
        """
            .. http:get:: /api/1/account/<int:id>

            Get a list of Accounts matching the given criteria

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/account/1 HTTP/1.1
                Host: example.com
                Accept: application/json, text/javascript

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    third_party: false,
                    name: "example_name",
                    notes: null,
                    number: "111111111111",
                    active: true,
                    id: 1,
                    s3_name: "example_name",
                    auth: {
                        authenticated: true,
                        user: "user@example.com"
                    }
                }

            :statuscode 200: no error
            :statuscode 401: Authentication failure. Please login.
        """
        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        result = Account.query.filter(Account.id==account_id).first()

        account_marshaled = marshal(result.__dict__, ACCOUNT_FIELDS)
        account_marshaled['auth'] = self.auth_dict

        return account_marshaled, 200, CORS_HEADERS

    def put(self, account_id):
        """
            .. http:put:: /api/1/account/1

            Edit an existing account.

            **Example Request**:

            .. sourcecode:: http

                PUT /api/1/account/1 HTTP/1.1
                Host: example.com
                Accept: application/json

                {
                    'name': 'edited_account'
                    's3_name': 'edited_account',
                    'number': '0123456789',
                    'notes': 'this account is for ...',
                    'active': true,
                    'third_party': false
                }

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    'name': 'edited_account'
                    's3_name': 'edited_account',
                    'number': '0123456789',
                    'notes': 'this account is for ...',
                    'active': true,
                    'third_party': false
                }

            :statuscode 200: no error
            :statuscode 401: Authentication Error. Please Login.
        """

        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        self.reqparse.add_argument('name', required=False, type=unicode, help='Must provide account name', location='json')
        self.reqparse.add_argument('s3_name', required=False, type=unicode, help='Will use name if s3_name not provided.', location='json')
        self.reqparse.add_argument('number', required=False, type=unicode, help='Add the account number if available.', location='json')
        self.reqparse.add_argument('notes', required=False, type=unicode, help='Add context.', location='json')
        self.reqparse.add_argument('active', required=False, type=bool, help='Determines whether this account should be interrogated by security monkey.', location='json')
        self.reqparse.add_argument('third_party', required=False, type=bool, help='Determines whether this account is a known friendly third party account.', location='json')
        args = self.reqparse.parse_args()

        account = Account.query.filter(Account.id == account_id).first()
        if account:
            account.name = args['name']
            account.s3_name = args['s3_name']
            account.number = args['number']
            account.notes = args['notes']
            account.active = args['active']
            account.third_party = args['third_party']
            db.session.add(account)
            db.session.commit()

            updated_account = Account.query.filter(Account.id == account_id).first()
            marshaled_account = marshal(updated_account.__dict__, ACCOUNT_FIELDS)
            marshaled_account['auth'] = self.auth_dict
        else:
            return {'status': 'error. Account ID not found.'}, 404, CORS_HEADERS

        return marshaled_account, 200, CORS_HEADERS


    def delete(self, account_id):
        """
            .. http:delete:: /api/1/account/1

            Delete an account.

            **Example Request**:

            .. sourcecode:: http

                DELETE /api/1/account/1 HTTP/1.1
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
        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        Account.query.filter(Account.id == account_id).delete()
        db.session.commit()

        return {'status': 'deleted'}, 202, CORS_HEADERS


class AccountPost(AuthenticatedService):
    def __init__(self):
        super(AccountPost, self).__init__()
        self.reqparse = reqparse.RequestParser()

    def post(self):
        """
            .. http:post:: /api/1/account/

            Create a new account.

            **Example Request**:

            .. sourcecode:: http

                POST /api/1/account/ HTTP/1.1
                Host: example.com
                Accept: application/json

                {
                    'name': 'new_account'
                    's3_name': 'new_account',
                    'number': '0123456789',
                    'notes': 'this account is for ...',
                    'active': true,
                    'third_party': false
                }

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 201 Created
                Vary: Accept
                Content-Type: application/json

                {
                    'name': 'new_account'
                    's3_name': 'new_account',
                    'number': '0123456789',
                    'notes': 'this account is for ...',
                    'active': true,
                    'third_party': false
                }

            :statuscode 201: created
            :statuscode 401: Authentication Error. Please Login.
        """
        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        self.reqparse.add_argument('name', required=True, type=unicode, help='Must provide account name', location='json')
        self.reqparse.add_argument('s3_name', required=False, type=unicode, help='Will use name if s3_name not provided.', location='json')
        self.reqparse.add_argument('number', required=False, type=unicode, help='Add the account number if available.', location='json')
        self.reqparse.add_argument('notes', required=False, type=unicode, help='Add context.', location='json')
        self.reqparse.add_argument('active', required=False, type=bool, help='Determines whether this account should be interrogated by security monkey.', location='json')
        self.reqparse.add_argument('third_party', required=False, type=bool, help='Determines whether this account is a known friendly third party account.', location='json')
        args = self.reqparse.parse_args()

        name = args['name']
        s3_name = args.get('s3_name', name)
        number = args.get('number', None)
        notes = args.get('notes', None)
        active = args.get('active', True)
        third_party = args.get('third_party', False)

        account = Account()
        account.name = name
        account.s3_name = s3_name
        account.number = number
        account.notes = notes
        account.active = active
        account.third_party = third_party
        db.session.add(account)
        db.session.commit()

        updated_account = Account.query.filter(Account.id == account.id).first()
        marshaled_account = marshal(updated_account.__dict__, ACCOUNT_FIELDS)
        marshaled_account['auth'] = self.auth_dict
        return marshaled_account, 201, CORS_HEADERS





class ItemAuditList(AuthenticatedService):
    def __init__(self):
        super(ItemAuditList, self).__init__()

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
                            justification: null,
                            name: "example_name",
                            technology: "s3",
                            issue: "Example Issue",
                            region: "us-east-1",
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
        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        self.reqparse.add_argument('count', type=int, default=30, location='args')
        self.reqparse.add_argument('page', type=int, default=1, location='args')
        self.reqparse.add_argument('regions', type=str, default=None, location='args')
        self.reqparse.add_argument('accounts', type=str, default=None, location='args')
        self.reqparse.add_argument('technologies', type=str, default=None, location='args')
        self.reqparse.add_argument('names', type=str, default=None, location='args')
        self.reqparse.add_argument('active', type=str, default=None, location='args')
        self.reqparse.add_argument('q', type=str, default=None, location='args')
        args = self.reqparse.parse_args()

        page = args.pop('page', None)
        count = args.pop('count', None)
        for k, v in args.items():
            if not v:
                del args[k]

        query = ItemAudit.query.join("item")
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
            query = query.join((ItemRevision, Item.latest_revision_id == ItemRevision.id))
            query = query.filter(ItemRevision.active == active)
        if 'q' in args:
            search = args['q']
            query = query.filter(
                (ItemAudit.issue.ilike('%{}%'.format(search))) |
                (ItemAudit.notes.ilike('%{}%'.format(search))) |
                (ItemAudit.justification.ilike('%{}%'.format(search))) |
                (Item.name.ilike('%{}%'.format(search)))
            )
        query = query.order_by(ItemAudit.justified, ItemAudit.score.desc())
        issues = query.paginate(page, count)

        marshaled_dict = {}
        marshaled_dict['page'] = issues.page
        marshaled_dict['total'] = issues.total
        marshaled_dict['auth'] = self.auth_dict

        items_marshaled = []
        for issue in issues.items:
            item_marshaled = marshal(issue.item.__dict__, ITEM_FIELDS)
            issue_marshaled = marshal(issue.__dict__, AUDIT_FIELDS)
            account_marshaled = {'account': issue.item.account.name}
            technology_marshaled = {'technology': issue.item.technology.name}
            if issue.justified:
                issue_marshaled = dict(
                    issue_marshaled.items() +
                    {'justified_user': issue.user.email}.items())
            merged_marshaled = dict(
                item_marshaled.items() +
                issue_marshaled.items() +
                account_marshaled.items() +
                technology_marshaled.items())
            items_marshaled.append(merged_marshaled)

        marshaled_dict['items'] = items_marshaled
        return marshaled_dict, 200, CORS_HEADERS


class ItemAuditGet(AuthenticatedService):
    def __init__(self):
        super(ItemAuditGet, self).__init__()

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
                    region: "us-east-1",
                    justified: false,
                    justified_date: null,
                    id: 704
                }

            :statuscode 200: no error
            :statuscode 401: Authentication Error. Please login.
        """

        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        query = ItemAudit.query.join("item").filter(ItemAudit.id == audit_id)
        result = query.first()

        issue_marshaled = marshal(result, AUDIT_FIELDS)
        item_marshaled = marshal(result.item, ITEM_FIELDS)
        issue_marshaled = dict(
            issue_marshaled.items() +
            item_marshaled.items() +
            {'auth': self.auth_dict}.items()
        )
        return issue_marshaled, 200, CORS_HEADERS


# Returns a list of most recent revisions
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
        return marshaled_dict, 200, CORS_HEADERS


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

        return retval, 200, CORS_HEADERS


class RevisionComment(AuthenticatedService):
    def __init__(self):
        super(RevisionComment, self).__init__()

    def post(self):
        """
            .. http:post:: /api/1/comment/revision

            Post a comment about a specific revision.

            **Example Request**:

            .. sourcecode:: http

                POST /api/1/comment/revision HTTP/1.1
                Host: example.com
                Accept: application/json

                {
                    'id': 1234,
                    'action': 'add_comment',
                    'comment': 'This revision is my favorite.'
                }

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "result": "success"
                }

            :statuscode 200: no error
            :statuscode 401: Authentication Error. Please Login.
        """

        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        self.reqparse.add_argument('comment', required=False, type=unicode, help='Must provide comment', location='json')
        self.reqparse.add_argument('action', required=True, type=str, help='Must provide action ("add_comment" or "remove_comment")', location='json')
        self.reqparse.add_argument('id', required=True, type=int, help='For adds, use revision id. For deletes, use comment id.', location='json')
        args = self.reqparse.parse_args()
        irc = None

        if args['action'] == 'add_comment':
            irc = ItemRevisionComment()
            irc.user_id = current_user.id
            irc.revision_id = args['id']
            irc.text = args['comment']
            irc.date_created = datetime.datetime.utcnow()
            db.session.add(irc)
            db.session.commit()
        elif args['action'] == 'remove_comment':
            query = ItemRevisionComment.query.filter(ItemRevisionComment.id == args['id'])
            query = query.filter(ItemRevisionComment.user_id == current_user.id).delete()
            db.session.commit()

        return {'result': 'success'}, 200, CORS_HEADERS


class ItemCommentView(AuthenticatedService):
    def __init__(self):
        super(ItemCommentView, self).__init__()

    def post(self):
        """
            .. http:post:: /api/1/comment/item/

            Add or remove an item comment.

            **Example Request**:

            .. sourcecode:: http

                POST /api/1/comment/item HTTP/1.1
                Host: example.com
                Accept: application/json

                {
                    'id': 1234,
                    'action': 'add_comment',
                    'comment': 'This item is my favorite.'
                }

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "result": "success"
                }

            :statuscode 200: no error
            :statuscode 401: Authentication Error. Please Login.
        """

        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        self.reqparse.add_argument('comment', required=False, type=unicode, help='Must provide comment', location='json')
        self.reqparse.add_argument('action', required=True, type=str, help='Must provide action ("add_comment" or "remove_comment")', location='json')
        self.reqparse.add_argument('id', required=True, type=int, help='For adds, use revision id. For deletes, use comment id.', location='json')
        args = self.reqparse.parse_args()
        ic = None

        if args['action'] == 'add_comment':
            ic = ItemComment()
            ic.user_id = current_user.id
            ic.item_id = args['id']
            ic.text = args['comment']
            ic.date_created = datetime.datetime.utcnow()
            db.session.add(ic)
            db.session.commit()
        elif args['action'] == 'remove_comment':
            query = ItemComment.query.filter(ItemComment.id == args['id'])
            query = query.filter(ItemComment.user_id == current_user.id).delete()
            db.session.commit()

        return {'result': 'success'}, 200, CORS_HEADERS


class Justify(AuthenticatedService):
    def __init__(self):
        super(Justify, self).__init__()

    def post(self, audit_id):
        """
            .. http:post:: /api/1/justify/1234

            Justify an audit issue on a specific item.

            **Example Request**:

            .. sourcecode:: http

                POST /api/1/justify/1234 HTTP/1.1
                Host: example.com
                Accept: application/json

                {
                    'action': 'justify',
                    'justification': 'I promise not to abuse this.'
                }

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "result": {
                        "justification": "I promise not to abuse this.",
                        "issue": "Example Issue",
                        "notes": "Example Notes",
                        "score": 0,
                        "item_id": 11890,
                        "justified_user": "user@example.com",
                        "justified": true,
                        "justified_date": "2014-06-19 21:45:58.779168",
                        "id": 1234
                    },
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

        self.reqparse.add_argument('justification', required=False, type=str, help='Must provide justification', location='json')
        self.reqparse.add_argument('action', required=True, type=str, help='Must provide action ("justify" or "remove_justification")', location='json')
        args = self.reqparse.parse_args()

        item = ItemAudit.query.filter(ItemAudit.id == audit_id).first()
        if not item:
            return {"Error": "Item with audit_id {} not found".format(audit_id)}, 404, CORS_HEADERS

        if args['action'].lower() == 'justify':
            item.justified_user_id = current_user.id
            item.justified = True
            item.justified_date = datetime.datetime.utcnow()
            item.justification = args['justification']
        elif args['action'].lower() == 'remove_justification':
            item.justified_user_id = None
            item.justified = False
            item.justified_date = None
            item.justification = None
        else:
            return {"Error": 'Must provide action ("justify" or "remove_justification")'}, 405, CORS_HEADERS

        db.session.add(item)
        db.session.commit()

        item2 = ItemAudit.query.filter(ItemAudit.id == audit_id).first()

        retdict = {}
        retdict['auth'] = self.auth_dict
        if item2.user:
            retdict['result'] = dict(
                marshal(item2.__dict__, AUDIT_FIELDS).items() +
                {"justified_user": item2.user.email}.items())
        else:
            retdict['result'] = dict(
                marshal(item2.__dict__, AUDIT_FIELDS).items() +
                {"justified_user": None}.items())

        return retdict, 200, CORS_HEADERS


class UserSettings(AuthenticatedService):
    def __init__(self):
        super(UserSettings, self).__init__()

    def get(self):
        """
            .. http:get:: /api/1/settings

            Get the settings for the given user.

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/settings HTTP/1.1
                Host: example.com
                Accept: application/json

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
                    "settings": [
                        {
                            "accounts": [
                                1,
                                2,
                                3,
                                6,
                                17,
                                21,
                                22
                            ],
                            "change_reports": "ISSUES",
                            "daily_audit_email": true
                        }
                    ]
                }

            :statuscode 200: no error
            :statuscode 401: Authentication Error. Please Authenticate.
        """
        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        return_dict = {}
        return_dict["auth"] = self.auth_dict
        if not current_user.is_authenticated():
            return_val = return_dict, 401, CORS_HEADERS
            return return_val

        return_dict["settings"] = []
        user = User.query.filter(User.id == current_user.get_id()).first()
        if user:
            sub_marshaled = marshal(user.__dict__, USER_SETTINGS_FIELDS)
            account_ids = []
            for account in user.accounts:
                account_ids.append(account.id)
            sub_marshaled = dict(sub_marshaled.items() +
                                 {"accounts": account_ids}.items()
                                 )
            return_dict["settings"].append(sub_marshaled)
        return return_dict, 200, CORS_HEADERS

    def post(self):
        """
            .. http:post:: /api/1/settings

            Change the settings for the current user.

            **Example Request**:

            .. sourcecode:: http

                POST /api/1/settings HTTP/1.1
                Host: example.com
                Accept: application/json

                {
                    "accounts": [
                        1,
                        2,
                        3,
                        6,
                        17,
                        21,
                        22
                    ],
                    "daily_audit_email": true,
                    "change_report_setting": "ALL"
                }

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
                    "settings": {
                        "accounts": [
                            1,
                            2,
                            3,
                            6,
                            17,
                            21,
                            22
                        ],
                        "daily_audit_email": true,
                        "change_report_setting": "ALL"
                    }
                }

            :statuscode 200: no error
            :statuscode 401: Authentication Error. Please Login.
        """

        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        self.reqparse.add_argument('accounts', required=True, type=list, help='Must provide accounts', location='json')
        self.reqparse.add_argument('change_report_setting', required=True, type=str, help='Must provide change_report_setting', location='json')
        self.reqparse.add_argument('daily_audit_email', required=True, type=bool, help='Must provide daily_audit_email', location='json')
        args = self.reqparse.parse_args()

        current_user.daily_audit_email = args['daily_audit_email']
        current_user.change_reports = args['change_report_setting']

        account_list = []
        for account_id in args['accounts']:
            account = Account.query.filter(Account.id == account_id).first()
            if account:
                account_list.append(account)
                #current_user.accounts.append(account)
        current_user.accounts = account_list

        db.session.add(current_user)
        db.session.commit()

        retdict = {}
        retdict['auth'] = self.auth_dict
        account_ids = []
        for account in current_user.accounts:
            account_ids.append(account.id)
        retdict['settings'] = {
            "accounts": account_ids,
            "change_report_setting": current_user.change_reports,
            "daily_audit_email": current_user.daily_audit_email
        }

        return retdict, 200, CORS_HEADERS


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
                            "issue_score": 0,
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

        marshaled_dict = {}
        marshaled_dict['page'] = items.page
        marshaled_dict['total'] = items.total
        marshaled_dict['auth'] = self.auth_dict

        marshaled_items = []
        for item in items.items:
            num_issues = len(item.issues)

            issue_score = 0
            for issue in item.issues:
                issue_score = issue_score + issue.score

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
                                              'active': active,
                                              'first_seen': first_seen,
                                              'last_seen': last_seen
                                          }.items())

            marshaled_items.append(item_marshaled)

        marshaled_dict['items'] = marshaled_items

        return marshaled_dict, 200, CORS_HEADERS
