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

from security_monkey import db
from security_monkey import app
from security_monkey.decorators import crossdomain

from flask.ext.restful import fields, marshal, Resource, reqparse
from flask.ext.login import current_user

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
    's3_name': fields.String,
    'number': fields.String,
    'notes': fields.String,
    'active': fields.Boolean,
    'third_party': fields.Boolean
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
        return True, ({"auth": auth_dict}, 401)
    return None, None
