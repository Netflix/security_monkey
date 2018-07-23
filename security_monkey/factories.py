import os

from flask import Flask
from flask_login import LoginManager


def setup_app(components):
    app = Flask(__name__, static_url_path='/static')

    # Set up the configuration
    setup_settings(app)

    for c in components:
        c.init_app(app)

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



def setup_routes():
    pass
