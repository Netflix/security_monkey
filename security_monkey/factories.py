import os
import stat

from flask import Flask

import sys
from logging import Formatter, handlers
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
from logging.config import dictConfig
from logging import DEBUG


# Use this handler to have log rotators give newly minted logfiles +gw perm
from security_monkey.extensions import db, lm, mail, rbac
from security_monkey.jirasync import JiraSync


class GroupWriteRotatingFileHandler(handlers.RotatingFileHandler):
    def doRollover(self):
        """
        Override base class method to make the new log file group writable.
        """
        # Rotate the file first.
        handlers.RotatingFileHandler.doRollover(self)

        # Add group write to the current permissions.
        try:
            currMode = os.stat(self.baseFilename).st_mode
            os.chmod(self.baseFilename, currMode | stat.S_IWGRP)
        except OSError:
            pass


handlers.GroupWriteRotatingFileHandler = GroupWriteRotatingFileHandler


def setup_app():
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

    return app


def setup_settings(app):
    """
    Sets up the configuration for Security Monkey

    :param app:
    :return:
    """
    # If SECURITY_MONKEY_SETTINGS is set, then use that.
    # Otherwise, use env-config/config.py
    if os.environ.get('SECURITY_MONKEY_SETTINGS'):
        app.config.from_envvar('SECURITY_MONKEY_SETTINGS')
    else:
        # find env-config/config.py
        from os.path import dirname, join, isfile
        path = dirname(dirname(__file__))
        path = join(path, 'env-config')
        path = join(path, 'config.py')

        if isfile(path):
            app.config.from_pyfile(path)
        else:
            print('PLEASE SET A CONFIG FILE WITH SECURITY_MONKEY_SETTINGS OR PUT ONE AT env-config/config.py')
            exit(-1)


def setup_extensions(app):
    db.init_app(app)
    lm.init_app(app)
    mail.init_app(app)
    rbac.init_app(app)

    # Optionals:
    try:
        from raven.contrib.flask import Sentry
        sentry = Sentry()
        sentry.init_app(app)
    except ImportError:
        app.logger.debug('Sentry not installed, skipping...')

    jirasync_file = os.environ.get('SECURITY_MONKEY_JIRA_SYNC')
    if jirasync_file:
        try:
            import security_monkey.extensions
            security_monkey.extensions.js = JiraSync(jirasync_file)
            security_monkey.extensions.js.init_app(app)
        except Exception as e:
            app.logger.error(repr(e))


def setup_logging(app):
    """
    Logging in security_monkey can be configured in two ways.

    1) Vintage: Set LOG_FILE and LOG_LEVEL in your config.
    LOG_FILE will default to stderr if no value is supplied.
    LOG_LEVEL will default to DEBUG if no value is supplied.

        LOG_LEVEL = "DEBUG"
        LOG_FILE = "/var/log/security_monkey/securitymonkey.log"

    2) Set LOG_CFG in your config to a PEP-0391 compatible
    logging configuration.

        LOG_CFG = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s %(levelname)s: %(message)s '
                        '[in %(pathname)s:%(lineno)d]'
                }
            },
            'handlers': {
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'DEBUG',
                    'formatter': 'standard',
                    'filename': '/var/log/security_monkey/securitymonkey.log',
                    'maxBytes': 10485760,
                    'backupCount': 100,
                    'encoding': 'utf8'
                },
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'DEBUG',
                    'formatter': 'standard',
                    'stream': 'ext://sys.stdout'
                }
            },
            'loggers': {
                'security_monkey': {
                    'handlers': ['file', 'console'],
                    'level': 'DEBUG'
                },
                'apscheduler': {
                    'handlers': ['file', 'console'],
                    'level': 'INFO'
                }
            }
        }
    """
    if not app.debug:
        if app.config.get('LOG_CFG'):
            # initialize the Flask logger (removes all handlers)
            _ = app.logger
            dictConfig(app.config.get('LOG_CFG'))
        else:
            # capability with previous config settings
            # Should have LOG_FILE and LOG_LEVEL set
            if app.config.get('LOG_FILE') is not None:
                handler = RotatingFileHandler(app.config.get('LOG_FILE'), maxBytes=10000000, backupCount=100)
            else:
                handler = StreamHandler(stream=sys.stderr)

            handler.setFormatter(
                Formatter('%(asctime)s %(levelname)s: %(message)s '
                          '[in %(pathname)s:%(lineno)d]')
            )
            app.logger.setLevel(app.config.get('LOG_LEVEL', DEBUG))
            app.logger.addHandler(handler)
