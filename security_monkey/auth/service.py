"""
.. module: security_monkey.auth.service
    :platform: Unix
    :copyright: (c) 2015 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.
.. moduleauthor:: Patrick Kelley <patrick@netflix.com>
.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""
from __future__ import unicode_literals

from datetime import timedelta, datetime
from functools import wraps

import jwt
import json
import binascii

from flask import g, current_app, request, jsonify
from flask_restful import Resource

from security_monkey.extensions import db

from flask_principal import identity_loaded, identity_changed, RoleNeed, UserNeed, Identity

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers

from security_monkey.datastore import User


def get_rsa_public_key(n, e):
    """
    Retrieve an RSA public key based on a module and exponent as provided by the JWKS format.
    :param n:
    :param e:
    :return: a RSA Public Key in PEM format
    """
    n = int(binascii.hexlify(jwt.utils.base64url_decode(bytes(n))), 16)
    e = int(binascii.hexlify(jwt.utils.base64url_decode(bytes(e))), 16)
    pub = RSAPublicNumbers(e, n).public_key(default_backend())
    return pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )


def fetch_token_header_payload(token):
    """
    Fetch the header and payload out of the JWT token.
    :param token:
    :return: :raise jwt.DecodeError:
    """
    token = token.encode('utf-8')
    try:
        signing_input, crypto_segment = token.rsplit(b'.', 1)
        header_segment, payload_segment = signing_input.split(b'.', 1)
    except ValueError:
        raise jwt.DecodeError('Not enough segments')

    try:
        header = json.loads(jwt.utils.base64url_decode(header_segment).decode('utf-8'))
    except TypeError as e:
        current_app.logger.exception(e)
        raise jwt.DecodeError('Invalid header padding')

    try:
        payload = json.loads(jwt.utils.base64url_decode(payload_segment).decode('utf-8'))
    except TypeError as e:
        current_app.logger.exception(e)
        raise jwt.DecodeError('Invalid payload padding')

    return (header, payload)


@identity_loaded.connect
def on_identity_loaded(sender, identity):
    """
    Sets the identity of a given option, assigns additional permissions based on
    the role that the user is a part of.
    :param sender:
    :param identity:
    """
    # load the user
    user = User.query.filter(User.id == identity.id).first()

    # add the UserNeed to the identity
    identity.provides.add(UserNeed(identity.id))

    # identity with the roles that the user provides
    if hasattr(user, 'roles'):
        for role in user.roles:
            identity.provides.add(RoleNeed(role.name))

    g.user = user


def setup_user(email, groups=None, default_role='View'):
    user = User.query.filter(User.email == email).first()
    if user:
        return user

    role = default_role
    groups = groups or []
    if groups:
        if current_app.config.get('ADMIN_GROUP') and current_app.config.get('ADMIN_GROUP') in groups:
            role = 'Admin'
        elif current_app.config.get('JUSTIFY_GROUP') and current_app.config.get('JUSTIFY_GROUP') in groups:
            role = 'Justify'
        elif current_app.config.get('VIEW_GROUP') and current_app.config.get('VIEW_GROUP') in groups:
            role = 'View'

    # If we get an sso user create them an account
    user = User()
    user.email = email
    user.active = True
    user.role = role

    db.session.add(user)
    db.session.commit()
    db.session.refresh(user)

    return user


def create_token(user):
    """
    Copypasta'd from Lemur

    Create a valid JWT for a given user/api key, this token is then used to authenticate
    sessions until the token expires.
    :param user:
    :return:
    """
    expiration_delta = timedelta(days=int(current_app.config.get('SM_TOKEN_EXPIRATION', 1)))
    payload = {
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + expiration_delta
    }

    # Handle Just a User ID & User Object.
    if isinstance(user, int):
        payload['sub'] = user
    else:
        payload['sub'] = user.id

    token = jwt.encode(payload, current_app.config['SECRET_KEY'])
    return token.decode('unicode_escape')


def login_required(f):
    """
    Copypasta'd from Lemur

    Validates the JWT and ensures that is has not expired and the user is still active.

    :param f:
    :return:
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.headers.get('Authorization'):
            response = jsonify(message='Missing authorization header')
            response.status_code = 401
            return response

        try:
            token = request.headers.get('Authorization').split()[1]
        except Exception:
            return dict(message='Token is invalid'), 403

        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'])
        except jwt.DecodeError:
            return dict(message='Token is invalid'), 403
        except jwt.ExpiredSignatureError:
            return dict(message='Token has expired'), 403
        except jwt.InvalidTokenError:
            return dict(message='Token is invalid'), 403

        user = user_service.get(payload['sub'])

        if not user.active:
            return dict(message='User is not currently active'), 403

        g.current_user = user

        if not g.current_user:
            return dict(message='You are not logged in'), 403

        # Tell Flask-Principal the identity changed
        identity_changed.send(current_app._get_current_object(), identity=Identity(g.current_user.id))

        return f(*args, **kwargs)

    return decorated_function


class AuthenticatedService(Resource):
    """
    Inherited by all resources that need to be protected by authentication.
    """
    method_decorators = [login_required]

    def __init__(self):
        super(AuthenticatedService, self).__init__()
