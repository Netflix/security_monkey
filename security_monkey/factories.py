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

from flask import Flask, jsonify

from werkzeug.exceptions import HTTPException

import security_monkey.extensions

from security_monkey.extensions import db, lm, mail, migrate, principal
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

    # Set up the blueprints:
    setup_blueprints(blueprints, app)

    # Error handlers:
    @app.errorhandler(Exception)
    def handle_error(e):
        code = 500
        if isinstance(e, HTTPException):
            code = e.code

        app.logger.exception(e)
        return jsonify(error=str(e)), code

    @app.errorhandler(403)
    def handle_error(e):
        return jsonify(error='Forbidden'), 403

    return app


def setup_settings(app):
    """
    Sets up the configuration for Security Monkey

    :param app:
    :return:
    """
    app.config.from_pyfile(resolve_app_config_path())

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


def setup_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    lm.init_app(app)
    mail.init_app(app)
    principal.init_app(app)

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


def setup_blueprints(blueprints, app):
    for b in blueprints:
        app.register_blueprint(b, url_prefix="/api/1")
