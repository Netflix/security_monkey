"""
.. module: security_monkey.sso.service
    :platform: Unix
    :copyright: (c) 2015 by Netflix Inc., see AUTHORS for more
    :license: Apache, see LICENSE for more details.
.. moduleauthor:: Patrick Kelley <patrick@netflix.com>
"""

import jwt
import json
import binascii

from flask import g, current_app

from flask_principal import identity_loaded, RoleNeed, UserNeed

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
    n = int(binascii.hexlify(jwt.utils.base64url_decode(bytes(n, encoding="utf-8"))), 16)
    e = int(binascii.hexlify(jwt.utils.base64url_decode(bytes(e, encoding="utf-8"))), 16)
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
    user = User.query.filter(User.id==identity.id).first()

    # add the UserNeed to the identity
    identity.provides.add(UserNeed(identity.id))

    # identity with the roles that the user provides
    if hasattr(user, 'roles'):
        for role in user.roles:
            identity.provides.add(RoleNeed(role.name))

    g.user = user


def setup_user(email, groups=None, default_role='View'):
    from security_monkey import app, db

    user = User.query.filter(User.email == email).first()
    if user:
        return user

    role = default_role
    groups = groups or []
    if groups:
        if app.config.get('ADMIN_GROUP') and app.config.get('ADMIN_GROUP') in groups:
            role = 'Admin'
        elif app.config.get('JUSTIFY_GROUP') and app.config.get('JUSTIFY_GROUP') in groups:
            role = 'Justify'
        elif app.config.get('VIEW_GROUP') and app.config.get('VIEW_GROUP') in groups:
            role = 'View'

    # if we get an sso user create them an account
    user = User(
        email=email,
        active=True,
        role=role
    )

    db.session.add(user)
    db.session.commit()
    db.session.refresh(user)

    return user
