import os
from os.path import dirname, join, isfile


def resolve_app_config_path():
    """If SECURITY_MONKEY_SETTINGS is set, then use that.

    Otherwise, use env-config/config.py

    :return:
    """
    if os.environ.get('SECURITY_MONKEY_SETTINGS'):
        path = os.environ['SECURITY_MONKEY_SETTINGS']
    else:
        # find env-config/config.py
        path = dirname(dirname(__file__))
        path = join(path, 'env-config')
        path = join(path, 'config.py')

    if isfile(path):
        return path
    else:
        print('[X] PLEASE SET A CONFIG FILE WITH SECURITY_MONKEY_SETTINGS OR PUT ONE AT env-config/config.py')
        exit(-1)
