#     Copyright 2018 Netflix, Inc.
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
"""
.. module: security_monkey.sso.header_auth
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Jordan Milne <jordan.milne@reddit.com>

"""

import functools

from flask import request
from flask_login import current_user
from flask_principal import Identity, identity_changed
from flask_security.utils import login_user

from security_monkey.sso.service import setup_user
from security_monkey import db


class HeaderAuthExtension(object):
    """
    Extension for handling login via authn headers set by a trusted reverse proxy
    """
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        orig_login = app.view_functions['security.login']

        # Wrap Flask-Security's login view with logic to try header-based authn
        @functools.wraps(orig_login)
        def _wrapped_login_view():
            if app.config.get("USE_HEADER_AUTH"):
                username_header_name = app.config["HEADER_AUTH_USERNAME_HEADER"]
                groups_header_name = app.config.get("HEADER_AUTH_GROUPS_HEADER")

                authed_user = request.headers.get(username_header_name)
                # Don't have a valid session but have a trusted authn header
                if not current_user.is_authenticated and authed_user:
                    groups = []
                    if groups_header_name and groups_header_name in request.headers:
                        groups = request.headers[groups_header_name].split(",")
                    user = setup_user(
                        authed_user,
                        groups=groups,
                        default_role=app.config.get('HEADER_AUTH_DEFAULT_ROLE', 'View')
                    )
                    # Tell Flask-Principal the identity changed
                    identity_changed.send(app, identity=Identity(user.id))
                    login_user(user)
                    db.session.commit()
                    db.session.refresh(user)

            return orig_login()

        # Tell the RBAC module that this view is meant to be reachable pre-auth
        rbac = app.extensions['rbac'].rbac
        rbac.exempt(_wrapped_login_view)

        # Replace Flask-Security's login endpoint with our wrapped version
        app.view_functions['security.login'] = _wrapped_login_view
