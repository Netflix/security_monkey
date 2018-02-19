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

from security_monkey import app
from flask_wtf.csrf import generate_csrf
from security_monkey.auth.models import RBACRole
from security_monkey.decorators import crossdomain

from flask_restful import fields, marshal, Resource, reqparse
from flask_login import current_user

ORIGINS = [
    'https://{}:{}'.format(app.config.get('FQDN'), app.config.get('WEB_PORT')),
    # Adding this next one so you can also access the dart UI by prepending /static to the path.
    'https://{}:{}'.format(app.config.get('FQDN'), app.config.get('API_PORT')),
    'https://{}:{}'.format(app.config.get('FQDN'), app.config.get('NGINX_PORT')),
    'https://{}:80'.format(app.config.get('FQDN'))
]

##### Marshal Datastructures #####

# Used by RevisionGet, RevisionList, ItemList
REVISION_FIELDS = {
    'id': fields.Integer,
    'date_created': fields.String,
    'date_last_ephemeral_change': fields.String,
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
    'fixed': fields.Boolean,
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
    'text': fields.String,
    'item_id': fields.Integer
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
    'identifier': fields.String,
    'notes': fields.String,
    'active': fields.Boolean,
    'third_party': fields.Boolean,
    'account_type': fields.String
}

USER_FIELDS = {
    'id': fields.Integer,
    'active': fields.Boolean,
    'email': fields.String,
    'role': fields.String,
    'confirmed_at': fields.String,
    'daily_audit_email': fields.Boolean,
    'change_reports': fields.String,
    'last_login_at': fields.String,
    'current_login_at': fields.String,
    'login_count': fields.Integer,
    'last_login_ip': fields.String,
    'current_login_ip': fields.String
}

ROLE_FIELDS = {
    'id': fields.Integer,
    'name': fields.String,
    'description': fields.String,
}

WHITELIST_FIELDS = {
    'id': fields.Integer,
    'name': fields.String,
    'notes': fields.String,
    'cidr': fields.String
}

IGNORELIST_FIELDS = {
    'id': fields.Integer,
    'prefix': fields.String,
    'notes': fields.String,
}

AUDITORSETTING_FIELDS = {
    'id': fields.Integer,
    'disabled': fields.Boolean,
    'issue_text': fields.String
}

ITEM_LINK_FIELDS = {
    'id': fields.Integer,
    'name': fields.String
}

AUDIT_SCORE_FIELDS = {
    'id': fields.Integer,
    'method': fields.String,
    'technology': fields.String,
    'score': fields.String,
    'disabled': fields.Boolean
}

ACCOUNT_PATTERN_AUDIT_SCORE_FIELDS = {
    'id': fields.Integer,
    'account_type': fields.String,
    'account_field': fields.String,
    'account_pattern': fields.String,
    'score': fields.String
}

WATCHER_CONFIG_FIELDS = {
    'id': fields.Integer,
    'index': fields.String,
    'interval': fields.String,
    'active': fields.Boolean
}


class AuthenticatedService(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(AuthenticatedService, self).__init__()
        self.auth_dict = dict()
        if current_user.is_authenticated:
            roles_marshal = []
            for role in current_user.roles:
                roles_marshal.append(marshal(role.__dict__, ROLE_FIELDS))

            roles_marshal.append({"name": current_user.role})

            for role in RBACRole.roles[current_user.role].get_parents():
                roles_marshal.append({"name": role.name})

            self.auth_dict = {
                "authenticated": True,
                "user": current_user.email,
                "roles": roles_marshal
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
    response.set_cookie('XSRF-COOKIE', generate_csrf())
    return response
