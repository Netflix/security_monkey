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
.. module: security_monkey
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""
import logging
import os

from flask import Flask, request, make_response
from flask_wtf.csrf import generate_csrf

from six import string_types
from functools import update_wrapper
from datetime import timedelta

import security_monkey.extensions

from security_monkey.extensions import db, lm, mail, migrate
from security_monkey.jirasync import JiraSync
from security_monkey.utils import resolve_app_config_path


def setup_app(blueprints):
    """
    Main factory to set up the Security Monkey application
    :return:
    """
    app = Flask(__name__, static_url_path='/static')

    # Set up the configuration
    setup_settings(app)

    # Logging:
    setup_logging(app)

    # Set up the extensions:
    setup_extensions(app)

    # Set up origins and other pre and post request code:
    setup_pre_and_post_requests(app)

    # Set up the blueprints:
    setup_blueprints(blueprints, app)

    return app


def setup_settings(app):
    """
    Sets up the configuration for Security Monkey

    :param app:
    :return:
    """
    app.config.from_pyfile(resolve_app_config_path())


def setup_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    lm.init_app(app)
    mail.init_app(app)

    # Optionals:
    try:
        from raven.contrib.flask import Sentry
        security_monkey.extensions.sentry = Sentry()
        security_monkey.extensions.sentry.init_app(app)
    except ImportError:
        app.logger.debug('Sentry not installed, skipping...')

    jirasync_file = os.environ.get('SECURITY_MONKEY_JIRA_SYNC')
    if jirasync_file:
        try:
            security_monkey.extensions.jirasync = JiraSync(jirasync_file)
            security_monkey.extensions.jirasync.init_app(app)
        except Exception as e:
            app.logger.error(repr(e))


def setup_logging(app):
    app._logger = logging.getLogger('security_monkey')

    if not app.config.get("DONT_IGNORE_BOTO_VERBOSE_LOGGERS"):
        logging.getLogger('botocore.vendored.requests.packages.urllib3').setLevel(logging.WARNING)
        logging.getLogger('botocore.credentials').setLevel(logging.WARNING)


def crossdomain(app=None, allowed_origins=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    """
    Add the necessary headers for CORS requests.
    Copied from http://flask.pocoo.org/snippets/56/ with minor modifications.
    From that URL:
        This snippet by Armin Ronacher can be used freely for anything you like. Consider it public domain.
    """
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, string_types):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(allowed_origins, string_types):
        allowed_origins = ', '.join(allowed_origins)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_origin(allowed_origins):
        origin = request.headers.get("Origin", None)
        if origin and app.config.get('DEBUG', False):
            return origin
        if origin and origin in allowed_origins:
            return origin

        return None

    def get_methods():
        if methods is not None:
            return methods

        options_resp = app.make_default_options_response()
        return options_resp.headers.get('allow', 'GET')

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = get_origin(allowed_origins)
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            h['Access-Control-Allow-Credentials'] = 'true'
            h['Access-Control-Allow-Headers'] = "Origin, X-Requested-With, Content-Type, Accept"
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


def setup_pre_and_post_requests(app):
    origins = [
        'https://{}:{}'.format(app.config.get('FQDN'), app.config.get('WEB_PORT')),
        # Adding this next one so you can also access the dart UI by prepending /static to the path.
        'https://{}:{}'.format(app.config.get('FQDN'), app.config.get('API_PORT')),
        'https://{}:{}'.format(app.config.get('FQDN'), app.config.get('NGINX_PORT')),
        'https://{}:80'.format(app.config.get('FQDN'))
    ]

    @app.after_request
    @crossdomain(app=app, allowed_origins=origins)
    def after(response):
        response.set_cookie('XSRF-COOKIE', generate_csrf())
        return response


def setup_blueprints(blueprints, app):
    for b in blueprints:
        app.register_blueprint(b, url_prefix="/api/1")
