"""
.. module: security_monkey.sso.views
    :platform: Unix
    :copyright: (c) 2015 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.
.. moduleauthor:: Patrick Kelley <patrick@netflix.com>
"""
import json
import base64
import uuid

import jwt
import requests

from flask import Blueprint, current_app, redirect, request

from flask_restful import reqparse, Resource, Api
from flask_principal import Identity, identity_changed
from flask_security.utils import login_user

try:
    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    from onelogin.saml2.utils import OneLogin_Saml2_Utils
    onelogin_import_success = True
except ImportError:
    onelogin_import_success = False

try:
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request as GoogleAuthTransportRequest
    google_import_success = True
except ImportError:
    google_import_success = False

from .service import fetch_token_header_payload, get_rsa_public_key, setup_user

from security_monkey.datastore import User
from security_monkey.exceptions import UnableToIssueGoogleAuthToken, UnableToAccessGoogleEmail
from security_monkey import db, rbac, csrf

from six.moves.urllib.parse import urlparse

mod = Blueprint('sso', __name__)
# SSO providers implement their own CSRF protection
csrf.exempt(mod)
api = Api(mod)

from flask_security.utils import validate_redirect_url


class Ping(Resource):
    """
    This class serves as an example of how one might implement an SSO provider for use with Security Monkey. In
    this example we use a OpenIDConnect authentication flow, that is essentially OAuth2 underneath.
    """
    decorators = [rbac.allow(["anonymous"], ["GET", "POST"])]
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(Ping, self).__init__()

    def get(self):
        return self.post()

    def post(self):
        if "ping" not in current_app.config.get("ACTIVE_PROVIDERS"):
            return "Ping is not enabled in the config.  See the ACTIVE_PROVIDERS section.", 404

        default_state = 'clientId,{client_id},redirectUri,{redirectUri},return_to,{return_to}'.format(
            client_id=current_app.config.get('PING_CLIENT_ID'),
            redirectUri=current_app.config.get('PING_REDIRECT_URI'),
            return_to=current_app.config.get('WEB_PATH')
        )
        self.reqparse.add_argument('code', type=str, required=True)
        self.reqparse.add_argument('state', type=str, required=False, default=default_state)

        args = self.reqparse.parse_args()
        client_id = args['state'].split(',')[1]
        redirect_uri = args['state'].split(',')[3]
        return_to = args['state'].split(',')[5]

        if not validate_redirect_url(return_to):
            return_to = current_app.config.get('WEB_PATH')

        # take the information we have received from the provider to create a new request
        params = {
            'client_id': client_id,
            'grant_type': 'authorization_code',
            'scope': 'openid email profile address',
            'redirect_uri': redirect_uri,
            'code': args['code']
        }

        # you can either discover these dynamically or simply configure them
        access_token_url = current_app.config.get('PING_ACCESS_TOKEN_URL')
        user_api_url = current_app.config.get('PING_USER_API_URL')

        # the secret and cliendId will be given to you when you signup for the provider
        basic = base64.b64encode(bytes('{0}:{1}'.format(client_id, current_app.config.get("PING_SECRET")), encoding="utf-8"))
        headers = {'Authorization': 'Basic {0}'.format(basic.decode('utf-8'))}

        # exchange authorization code for access token.
        r = requests.post(access_token_url, headers=headers, params=params)
        id_token = r.json()['id_token']
        access_token = r.json()['access_token']

        # fetch token public key
        header_data = fetch_token_header_payload(id_token)[0]
        jwks_url = current_app.config.get('PING_JWKS_URL')

        # retrieve the key material as specified by the token header
        r = requests.get(jwks_url)
        for key in r.json()['keys']:
            if key['kid'] == header_data['kid']:
                secret = get_rsa_public_key(key['n'], key['e'])
                algo = header_data['alg']
                break
        else:
            return dict(message='Key not found'), 403

        # validate your token based on the key it was signed with
        try:
            jwt.decode(id_token, secret.decode('utf-8'), algorithms=[algo], audience=client_id)
        except jwt.DecodeError:
            return dict(message='Token is invalid'), 403
        except jwt.ExpiredSignatureError:
            return dict(message='Token has expired'), 403
        except jwt.InvalidTokenError:
            return dict(message='Token is invalid'), 403

        user_params = dict(access_token=access_token, schema='profile')

        # retrieve information about the current user.
        r = requests.get(user_api_url, params=user_params)
        profile = r.json()

        user = setup_user(
            profile.get('email'),
            profile.get('groups', profile.get('googleGroups', [])),
            current_app.config.get('PING_DEFAULT_ROLE', 'View'))

        # Tell Flask-Principal the identity changed
        identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
        login_user(user)
        db.session.commit()
        db.session.refresh(user)

        return redirect(return_to, code=302)


class AzureAD(Resource):
    """
    This class serves as an example of how one might implement an SSO provider for use with Security Monkey. In
    this example we use a OpenIDConnect authentication flow, that is essentially OAuth2 underneath.
    """
    decorators = [rbac.allow(["anonymous"], ["GET", "POST"])]
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(AzureAD, self).__init__()

    def get(self):
        return self.post()

    def get_idp_cert(self, id_token, jwks_url):
        header_data = fetch_token_header_payload(id_token)[0]
        # retrieve the key material as specified by the token header
        r = requests.get(jwks_url)
        for key in r.json()['keys']:
            if key['kid'] == header_data['kid']:
                secret = get_rsa_public_key(key['n'], key['e'])
                algo = header_data['alg']
                return secret, algo
        else:
            return dict(message='Key not found'), 403

    def validate_id_token(self, id_token, client_id, jwks_url):
        # validate your token based on the key it was signed with
        try:
            (secret, algo) = self.get_idp_cert(id_token, jwks_url)
            token = jwt.decode(id_token, secret.decode('utf-8'), algorithms=[algo], audience=client_id)
            if 'upn' in token:
                return token['upn']
            elif 'email' in token:
                return token['email']
            else:
                return dict(message="Unable to obtain user information from token")
        except jwt.DecodeError:
            return dict(message='Token is invalid'), 403
        except jwt.ExpiredSignatureError:
            return dict(message='Token has expired'), 403
        except jwt.InvalidTokenError:
            return dict(message='Token is invalid'), 403

    def post(self):
        if "aad" not in current_app.config.get("ACTIVE_PROVIDERS"):
            return "AzureAD is not enabled in the config.  See the ACTIVE_PROVIDERS section.", 404

        default_state = 'clientId,{client_id},redirectUri,{redirectUri},return_to,{return_to}'.format(
            client_id=current_app.config.get('AAD_CLIENT_ID'),
            redirectUri=current_app.config.get('AAD_REDIRECT_URI'),
            return_to=current_app.config.get('WEB_PATH')
        )
        self.reqparse.add_argument('code', type=str, required=True)
        self.reqparse.add_argument('id_token', type=str, required=True)
        self.reqparse.add_argument('state', type=str, required=False, default=default_state)

        args = self.reqparse.parse_args()
        client_id = args['state'].split(',')[1]
        redirect_uri = args['state'].split(',')[3]
        return_to = args['state'].split(',')[5]
        id_token = args['id_token']

        if not validate_redirect_url(return_to):
            return_to = current_app.config.get('WEB_PATH')

        # fetch token public key
        jwks_url = current_app.config.get('AAD_JWKS_URL')

        # Validate id_token and extract username (email)
        username = self.validate_id_token(id_token, client_id, jwks_url)

        user = setup_user(username, '', current_app.config.get('AAD_DEFAULT_ROLE', 'View'))

        # Tell Flask-Principal the identity changed
        identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
        login_user(user)
        db.session.commit()
        db.session.refresh(user)

        return redirect(return_to, code=302)


class Google(Resource):
    decorators = [rbac.allow(["anonymous"], ["GET", "POST"])]
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(Google, self).__init__()

        if self._isAuthMethod('directory'):
            try:
                creds = service_account.Credentials.from_service_account_file(
                    current_app.config.get("GOOGLE_DOMAIN_WIDE_DELEGATION_KEY_PATH"),
                    scopes=['https://www.googleapis.com/auth/admin.directory.group.readonly'])
            except OSError:    
                creds = service_account.Credentials.from_service_account_info(
                    json.loads(current_app.config.get("GOOGLE_DOMAIN_WIDE_DELEGATION_KEY_JSON")),
                    scopes=['https://www.googleapis.com/auth/admin.directory.group.readonly'])
            self.credentials = creds.with_subject(current_app.config.get("GOOGLE_DOMAIN_WIDE_DELEGATION_SUBJECT"))

    def _isAuthMethod(self, method):
        return current_app.config.get("GOOGLE_AUTH_API_METHOD").lower() == method

    def get(self):
        return self.post()

    def post(self):
        if "google" not in current_app.config.get("ACTIVE_PROVIDERS"):
            return "Google is not enabled in the config.  See the ACTIVE_PROVIDERS section.", 404

        default_state = 'clientId,{client_id},redirectUri,{redirectUri},return_to,{return_to}'.format(
            client_id=current_app.config.get("GOOGLE_CLIENT_ID"),
            redirectUri=api.url_for(Google),
            return_to=current_app.config.get('WEB_PATH')
        )
        self.reqparse.add_argument('code', type=str, required=True)
        self.reqparse.add_argument('state', type=str, required=False, default=default_state)

        args = self.reqparse.parse_args()
        client_id = args['state'].split(',')[1]
        redirect_uri = args['state'].split(',')[3]
        return_to = args['state'].split(',')[5]

        if not validate_redirect_url(return_to):
            return_to = current_app.config.get('WEB_PATH')

        access_token_url = 'https://accounts.google.com/o/oauth2/token'

        if self._isAuthMethod('directory'):
            auth_method_api_url = 'https://www.googleapis.com/admin/directory/v1/groups'
        elif self._isAuthMethod('people'):
            auth_method_api_url = 'https://www.googleapis.com/userinfo/v2/me'
        else:
            return dict(message='Auth method not supported'), 403

        args = self.reqparse.parse_args()

        # Step 1. Exchange authorization code for access token
        payload = {
            'client_id': client_id,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'code': args['code'],
            'client_secret': current_app.config.get('GOOGLE_SECRET')
        }

        r = requests.post(access_token_url, data=payload)
        token = r.json()

        if 'error' in token:
            raise UnableToIssueGoogleAuthToken(token['error'])

        # Step 1bis. Validate (some information of) the id token (if necessary)
        google_hosted_domain = current_app.config.get("GOOGLE_HOSTED_DOMAIN")
        userKey = None
        if google_hosted_domain is not None:
            current_app.logger.debug('We need to verify that the token was issued for this hosted domain: %s ' % (google_hosted_domain))

            # Get the JSON Web Token
            id_token = token['id_token']
            current_app.logger.debug('The id_token is: %s' % (id_token))

            # Extract the payload
            (header_data, payload_data) = fetch_token_header_payload(id_token)
            current_app.logger.debug('id_token.header_data: %s' % (header_data))
            current_app.logger.debug('id_token.payload_data: %s' % (payload_data))

            token_hd = payload_data.get('hd')
            if token_hd != google_hosted_domain:
                current_app.logger.debug('Verification failed: %s != %s' % (token_hd, google_hosted_domain))
                return dict(message='Token is invalid %s' % token), 403
            current_app.logger.debug('Verification passed')
            userKey = payload_data.get('email')

        # Step 2. Retrieve information about the current user
        if self._isAuthMethod('directory'):
            if not self.credentials.token:
                current_app.logger.debug('Attempting refresh credentials to obtain initial access token')
                self.credentials.refresh(GoogleAuthTransportRequest())

            headers = {'Authorization': 'Bearer {0}'.format(self.credentials.token)}

            api_url = "%(url)s?domain=%(domain)s&userKey=%(email)s&fields=groups/email" % {'url': auth_method_api_url,
                                                                                           'domain': google_hosted_domain,
                                                                                           'email': userKey}
            r = requests.get(api_url, headers=headers)
            groups = r.json()
            current_app.logger.debug('authenticated user with groups: %s' % groups)
            if len(groups.get('groups', [])) == 0:
                return dict(message='Groups association is invald for %s' % userKey), 403
            else:
                groupsEmails = [o['email'] for o in groups.get('groups', [])]
                default_role = current_app.config.get('GOOGLE_DEFAULT_ROLE', 'View')

                if current_app.config.get('GOOGLE_ADMIN_ROLE_GROUP_NAME') and \
                        current_app.config.get('GOOGLE_ADMIN_ROLE_GROUP_NAME') in groupsEmails:
                    default_role = "Admin"

                current_app.logger.debug('Authenticating user %s as role %s' % (userKey, default_role))
                user = setup_user(userKey, groupsEmails, default_role)

                # Tell Flask-Principal the identity changed
                identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
                login_user(user)
                db.session.commit()
                db.session.refresh(user)

                return redirect(return_to, code=302)
        elif self._isAuthMethod('people'):
            headers = {'Authorization': 'Bearer {0}'.format(token['access_token'])}

            r = requests.get(auth_method_api_url, headers=headers)
            r.raise_for_status()
            profile = r.json()

            if 'email' not in profile:
                raise UnableToAccessGoogleEmail()

            user = setup_user(profile.get('email'), profile.get('groups', []),
                              current_app.config.get('GOOGLE_DEFAULT_ROLE', 'View'))

            # Tell Flask-Principal the identity changed
            identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
            login_user(user)
            db.session.commit()
            db.session.refresh(user)

            return redirect(return_to, code=302)


class OneLogin(Resource):
    decorators = [rbac.allow(["anonymous"], ["GET", "POST"])]
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.req = OneLogin.prepare_from_flask_request(request)
        super(OneLogin, self).__init__()

    @staticmethod
    def prepare_from_flask_request(req):
        url_data = urlparse(req.url)
        return {
            'http_host': req.host,
            'server_port': url_data.port,
            'script_name': req.path,
            'get_data': req.args.copy(),
            'post_data': req.form.copy(),
            'https': ("on" if current_app.config.get("ONELOGIN_HTTPS") else "off")
    }

    def get(self):
        return self.post()

    def _consumer(self, auth):
        auth.process_response()
        errors = auth.get_errors()

        if not errors:
            if auth.is_authenticated:
                return True
            else:
                return False
        else:
            last_error_reason = auth.get_last_error_reason()
            current_app.logger.error('Error processing %s. Error reason: %s' % (', '.join(errors), last_error_reason))

            if current_app.config.get('ONELOGIN_LOG_SAML_RESPONSE'):
                auth_response = auth.get_last_response_xml()
                current_app.logger.debug('SAML response: %s' % auth_response)

            return False

    def post(self):
        if "onelogin" not in current_app.config.get("ACTIVE_PROVIDERS"):
            return "Onelogin is not enabled in the config.  See the ACTIVE_PROVIDERS section.", 404
        auth = OneLogin_Saml2_Auth(self.req, current_app.config.get("ONELOGIN_SETTINGS"))

        self.reqparse.add_argument('return_to', required=False, default=current_app.config.get('WEB_PATH'))
        self.reqparse.add_argument('acs', required=False)
        self.reqparse.add_argument('sls', required=False)

        args = self.reqparse.parse_args()

        return_to = args['return_to']

        if args['acs'] != None:
            # valids the SAML response and checks if successfully authenticated
            if self._consumer(auth):
                email = auth.get_attribute(current_app.config.get("ONELOGIN_EMAIL_FIELD"))[0]
                user = User.query.filter(User.email == email).first()

                # if we get an sso user create them an account
                if not user:
                    user = User(
                        email=email,
                        active=True,
                        role=current_app.config.get('ONELOGIN_DEFAULT_ROLE')
                        # profile_picture=profile.get('thumbnailPhotoUrl')
                    )
                    db.session.add(user)
                    db.session.commit()
                    db.session.refresh(user)

                # Tell Flask-Principal the identity changed
                identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
                login_user(user)
                db.session.commit()
                db.session.refresh(user)

                self_url = OneLogin_Saml2_Utils.get_self_url(self.req)
                if 'RelayState' in request.form and self_url != request.form['RelayState']:
                    return redirect(auth.redirect_to(request.form['RelayState']), code=302)
                else:
                    return redirect(current_app.config.get('BASE_URL'), code=302)
            else:
                return dict(message='OneLogin authentication failed.'), 403
        elif args['sls'] != None:
            return dict(message='OneLogin SLS not implemented yet.'), 405
        else:
            return redirect(auth.login(return_to=return_to))


class Okta(Resource):
    decorators = [rbac.allow(["anonymous"], ["GET", "POST"])]
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(Okta, self).__init__()

    def get(self):
        return self.post()

    def post(self):
        if "okta" not in current_app.config.get("ACTIVE_PROVIDERS"):
            return "Okta is not enabled in the config.  See the ACTIVE_PROVIDERS section.", 404

        default_state = 'clientId,{client_id},redirectUri,{redirectUri},return_to,{return_to}'.format(
            client_id=current_app.config.get('OKTA_CLIENT_ID'),
            redirectUri=current_app.config.get('OKTA_REDIRECT_URI'),
            return_to=current_app.config.get('WEB_PATH')
        )

        self.reqparse.add_argument('code', type=str, required=False)
        self.reqparse.add_argument('state', type=str, required=False, default=default_state)

        args = self.reqparse.parse_args()
        client_id = args['state'].split(',')[1]
        redirect_uri = args['state'].split(',')[3]
        return_to = args['state'].split(',')[5]
        code = args['code']

        if not validate_redirect_url(return_to):
            return_to = current_app.config.get('WEB_PATH')

        basic = base64.b64encode(bytes('{0}:{1}'.format(client_id, current_app.config.get("OKTA_CLIENT_SECRET")), encoding="utf-8"))
        headers = {
            'Authorization': 'Basic {0}'.format(basic.decode('utf-8')),
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        access_token_url = current_app.config.get('OKTA_TOKEN_ENDPOINT')
        params = {
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }

        r = requests.post(access_token_url, headers=headers, params=params)
        id_token = r.json()['id_token']

        # fetch token public key
        header_data = fetch_token_header_payload(id_token)[0]
        jwks_url = current_app.config.get('OKTA_JWKS_URI')

        # retrieve the key material as specified by the token header
        r = requests.get(jwks_url)
        for key in r.json()['keys']:
            if key['kid'] == header_data['kid']:
                secret = get_rsa_public_key(key['n'], key['e'])
                algo = header_data['alg']
                break
        else:
            return dict(message='Key not found'), 403

        # Validate your token based on the key it was signed with
        try:
            valid_token = jwt.decode(id_token, secret.decode('utf-8'), algorithms=[algo], audience=client_id)
        except jwt.DecodeError:
            return dict(message='Token is invalid'), 403
        except jwt.ExpiredSignatureError:
            return dict(message='Token has expired'), 403
        except jwt.InvalidTokenError:
            return dict(message='Token is invalid'), 403

        user = setup_user(valid_token['email'], '', current_app.config.get('OKTA_DEFAULT_ROLE', 'View'))

        # Tell Flask-Principal the identity changed
        identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
        login_user(user)
        db.session.commit()
        db.session.refresh(user)

        return redirect(return_to, code=302)


class Providers(Resource):
    decorators = [rbac.allow(["anonymous"], ["GET"])]
    def __init__(self):
        super(Providers, self).__init__()

    def get(self):
        active_providers = []

        nonce = uuid.uuid4().hex

        for provider in current_app.config.get("ACTIVE_PROVIDERS"):
            provider = provider.lower()

            if provider == "ping":
                active_providers.append({
                    'name': current_app.config.get("PING_NAME"),
                    'url': current_app.config.get('PING_REDIRECT_URI'),
                    'redirectUri': current_app.config.get("PING_REDIRECT_URI"),
                    'clientId': current_app.config.get("PING_CLIENT_ID"),
                    'responseType': 'code',
                    'scope': ['openid', 'profile', 'email'],
                    'scopeDelimiter': ' ',
                    'authorizationEndpoint': current_app.config.get("PING_AUTH_ENDPOINT"),
                    'requiredUrlParams': ['scope'],
                    'type': '2.0'
                })
            elif provider == "aad":
                active_providers.append({
                    'name': current_app.config.get("AAD_NAME"),
                    'url': current_app.config.get('AAD_REDIRECT_URI'),
                    'redirectUri': current_app.config.get("AAD_REDIRECT_URI"),
                    'clientId': current_app.config.get("AAD_CLIENT_ID"),
                    'nonce': nonce,
                    'responseType': 'id_token+code',
                    'response_mode': 'form_post',
                    'scope': ['email'],
                    'authorizationEndpoint': current_app.config.get("AAD_AUTH_ENDPOINT"),
                })
            elif provider == "google":
                google_provider = {
                    'name': 'google',
                    'clientId': current_app.config.get("GOOGLE_CLIENT_ID"),
                    'url': api.url_for(Google, _external=True, _scheme='https'),
                    'redirectUri': api.url_for(Google, _external=True, _scheme='https'),
                    'authorizationEndpoint': current_app.config.get("GOOGLE_AUTH_ENDPOINT"),
                    'scope': ['openid email'],
                    'responseType': 'code'
                }
                google_hosted_domain = current_app.config.get("GOOGLE_HOSTED_DOMAIN")
                if google_hosted_domain is not None:
                    google_provider['hd'] = google_hosted_domain
                active_providers.append(google_provider)
            elif provider == "onelogin":
                active_providers.append({
                    'name': 'OneLogin',
                    'authorizationEndpoint': api.url_for(OneLogin)
                })
            elif provider == "okta":
                active_providers.append({
                    'name': current_app.config.get("OKTA_NAME"),
                    'url': current_app.config.get("OKTA_REDIRECT_URI"),
                    'redirectUri': current_app.config.get("OKTA_REDIRECT_URI"),
                    'clientId': current_app.config.get("OKTA_CLIENT_ID"),
                    'responseType': 'code',
                    'scope': ['openid', 'email'],
                    'nonce': nonce,
                    'scopeDelimiter': ' ',
                    'authorizationEndpoint': current_app.config.get('OKTA_AUTH_ENDPOINT'),
                })
            else:
                raise Exception("Unknown authentication provider: {0}".format(provider))

        return active_providers


api.add_resource(AzureAD, '/auth/aad', endpoint='aad')
api.add_resource(Ping, '/auth/ping', endpoint='ping')
api.add_resource(Okta, '/auth/okta', endpoint='okta')
api.add_resource(Providers, '/auth/providers', endpoint='providers')

if google_import_success:
    api.add_resource(Google, '/auth/google', endpoint='google')

if onelogin_import_success:
    api.add_resource(OneLogin, '/auth/onelogin', endpoint='onelogin')
