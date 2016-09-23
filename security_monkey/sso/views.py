"""
.. module: security_monkey.sso.views
    :platform: Unix
    :copyright: (c) 2015 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.
.. moduleauthor:: Patrick Kelley <patrick@netflix.com>
"""
import jwt
import base64
import requests

from flask import Blueprint, current_app, redirect

from flask.ext.restful import reqparse, Resource, Api
from flask.ext.principal import Identity, identity_changed
from flask_login import login_user

from .service import fetch_token_header_payload, get_rsa_public_key

from security_monkey.datastore import User
from security_monkey import db, rbac


mod = Blueprint('sso', __name__)
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
        basic = base64.b64encode(bytes('{0}:{1}'.format(client_id, current_app.config.get("PING_SECRET"))))
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
            current_app.logger.debug(id_token)
            current_app.logger.debug(secret)
            current_app.logger.debug(algo)
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

        user = User.query.filter(User.email==profile['email']).first()

        # if we get an sso user create them an account
        if not user:
            user = User(
                email=profile['email'],
                active=True,
                role='View'
                # profile_picture=profile.get('thumbnailPhotoUrl')
            )
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)

        # Tell Flask-Principal the identity changed
        identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
        login_user(user)

        return redirect(return_to, code=302)


class Google(Resource):
    decorators = [rbac.allow(["anonymous"], ["GET", "POST"])]
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(Google, self).__init__()

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
        people_api_url = 'https://www.googleapis.com/plus/v1/people/me/openIdConnect'

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

        # Step 1bis. Validate (some information of) the id token (if necessary)
        google_hosted_domain = current_app.config.get("GOOGLE_HOSTED_DOMAIN")
        if google_hosted_domain is not None:
            current_app.logger.debug('We need to verify that the token was issued for this hosted domain: %s ' % (google_hosted_domain))

	    # Get the JSON Web Token
            id_token = r.json()['id_token']
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

        # Step 2. Retrieve information about the current user
        headers = {'Authorization': 'Bearer {0}'.format(token['access_token'])}

        r = requests.get(people_api_url, headers=headers)
        profile = r.json()

        user = User.query.filter(User.email == profile['email']).first()

        # if we get an sso user create them an account
        if not user:
            user = User(
                email=profile['email'],
                active=True,
                role='View'
                # profile_picture=profile.get('thumbnailPhotoUrl')
            )
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)

        # Tell Flask-Principal the identity changed
        identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
        login_user(user)

        return redirect(return_to, code=302)


class Providers(Resource):
    decorators = [rbac.allow(["anonymous"], ["GET"])]
    def __init__(self):
        super(Providers, self).__init__()

    def get(self):
        active_providers = []

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
            else:
                raise Exception("Unknown authentication provider: {0}".format(provider))

        return active_providers


api.add_resource(Ping, '/auth/ping', endpoint='ping')
api.add_resource(Google, '/auth/google', endpoint='google')
api.add_resource(Providers, '/auth/providers', endpoint='providers')
