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
from flask_restful import fields

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


# RBAC RBAC RBAC
# class AuthenticatedService(Resource):
#     def __init__(self):
#         self.reqparse = reqparse.RequestParser()
#         super(AuthenticatedService, self).__init__()
#         self.auth_dict = dict()
#         if current_user.is_authenticated:
#             roles_marshal = []
#             for role in current_user.roles:
#                 roles_marshal.append(marshal(role.__dict__, ROLE_FIELDS))
#
#             roles_marshal.append({"name": current_user.role})
#
#             # for role in RBACRole.roles[current_user.role].get_parents():
#             #     roles_marshal.append({"name": role.name})
#
#             self.auth_dict = {
#                 "authenticated": True,
#                 "user": current_user.email,
#                 "roles": roles_marshal
#             }
#         else:
#             if current_app.config.get('FRONTED_BY_NGINX'):
#                 url = "https://{}:{}{}".format(current_app.config.get('FQDN'), current_app.config.get('NGINX_PORT'), '/login')
#             else:
#                 url = "http://{}:{}{}".format(current_app.config.get('FQDN'), current_app.config.get('API_PORT'), '/login')
#             self.auth_dict = {
#                 "authenticated": False,
#                 "user": None,
#                 "url": url
#             }
