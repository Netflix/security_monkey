"""
.. module: security_monkey.decorators
    :synopsis: Defines decorators allowing for credentialed CORS access.

.. version:: $$VERSION$$
.. moduleauthor:: Armin Ronacher (http://flask.pocoo.org/snippets/56/)

"""

from datetime import timedelta
from itertools import product

from flask import make_response, request, current_app
from functools import update_wrapper, wraps

from security_monkey.datastore import Account
from security_monkey.exceptions import BotoConnectionIssue

from functools import wraps
import boto
import botocore
import time


def crossdomain(allowed_origins=None, methods=None, headers=None,
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
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(allowed_origins, basestring):
        allowed_origins = ', '.join(allowed_origins)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_origin(allowed_origins):
        origin = request.headers.get("Origin", None)
        if origin and current_app.config.get('DEBUG', False):
            return origin
        if origin and origin in allowed_origins:
            return origin

        return None

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers.get('allow', 'GET')

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
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


def record_exception():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                index = kwargs.get('index')
                account = kwargs.get('account_name')
                # Allow the recording region to be overridden for universal tech like IAM
                region = kwargs.get('exception_record_region') or kwargs.get('region')
                name = kwargs.get('name')
                exception_map = kwargs.get('exception_map')
                exc = BotoConnectionIssue(str(e), index, account, name)
                if name:
                    exception_map[(index, account, region, name)] = exc
                elif region:
                    exception_map[(index, account, region)] = exc
                elif account:
                    exception_map[(index, account)] = exc
                else:
                    exception_map[(index, )] = exc
        return decorated_function
    return decorator


def iter_account_region(index=None, accounts=None, regions=None):
    regions = regions or ['us-east-1']

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            item_list = []; exception_map = {}
            for account_name, region in product(accounts, regions):
                account = Account.query.filter(Account.name == account_name).first()
                if not account:
                    print "Couldn't find account with name",account_name
                    return
                kwargs['index'] = index
                kwargs['account_name'] = account.name
                kwargs['account_number'] = account.number
                kwargs['region'] = region
                kwargs['assume_role'] = account.role_name or 'SecurityMonkey'
                itm, exc = f(*args, **kwargs)
                item_list.extend(itm)
                exception_map.update(exc)
            return item_list, exception_map
        return decorated_function
    return decorator
