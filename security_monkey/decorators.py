"""
.. module: security_monkey.decorators
    :synopsis: Defines decorators allowing for credentialed CORS access.

.. version:: $$VERSION$$
.. moduleauthor:: Armin Ronacher (http://flask.pocoo.org/snippets/56/)

"""

from datetime import timedelta

from flask import make_response, request, current_app
from functools import update_wrapper, wraps

from six import string_types

from security_monkey.datastore import Account, store_exception
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey import app, sentry, AWS_DEFAULT_REGION, ARN_PREFIX, ARN_PARTITION

import boto3


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
    if headers is not None and not isinstance(headers, string_types):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(allowed_origins, string_types):
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


def record_exception(source="boto", pop_exception_fields=False):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # prevent these from being passed to the wrapped function:
            m = kwargs.pop if pop_exception_fields else kwargs.get
            exception_values = {
                'index': m('index'),
                'account': m('account_name', None),
                'exception_record_region': m('exception_record_region', None),
                'name': m('name', None),
                'exception_map': m('exception_map', {})
            }
            try:
                return f(*args, **kwargs)
            except Exception as e:
                if sentry:
                    sentry.captureException()
                index = exception_values['index']
                account = exception_values['account']
                # Allow the recording region to be overridden for universal tech like IAM
                region = exception_values['exception_record_region'] or kwargs.get('region')
                name = exception_values['name']
                exception_map = exception_values['exception_map']
                exc = BotoConnectionIssue(str(e), index, account, name)
                if name:
                    location = (index, account, region, name)
                elif region:
                    location = (index, account, region)
                elif account:
                    location = (index, account)
                else:
                    location = (index, )

                exception_map[location] = exc

                # Store the exception (the original one passed in, not exc):
                store_exception(source=source, location=location, exception=e)

        return decorated_function

    return decorator


def iter_account_region(index=None, accounts=None, service_name=None, exception_record_region=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            item_list = []
            exception_map = {}
            for account_name in accounts:
                account = Account.query.filter(Account.name == account_name).first()
                if not account:
                    app.logger.error("Couldn't find account with name {}".format(account_name))
                    return

                try:
                    (role, regions) = get_regions(account, service_name)
                except Exception as e:
                    exc = BotoConnectionIssue(str(e), index, account.name, None)
                    exception_map[(index, account)] = exc
                    return item_list, exception_map

                for region in regions:
                    kwargs['index'] = index
                    kwargs['account_name'] = account.name
                    kwargs['account_number'] = account.identifier
                    kwargs['region'] = region
                    kwargs['assume_role'] = account.getCustom("role_name") or 'SecurityMonkey'
                    if role:
                        kwargs['assumed_role'] = role or 'SecurityMonkey'
                    kwargs['exception_map'] = {}
                    if exception_record_region:
                        kwargs['exception_record_region'] = exception_record_region
                    itm, exc = f(*args, **kwargs)
                    item_list.extend(itm)
                    exception_map.update(exc)
            return item_list, exception_map
        return decorated_function
    return decorator


def get_regions(account, service_name):
    if not service_name:
        return None, [AWS_DEFAULT_REGION]

    sts = boto3.client('sts')
    role_name = 'SecurityMonkey'
    external_id = None
    if account.getCustom("role_name") and account.getCustom("role_name") != '':
        role_name = account.getCustom("role_name")
    if account.getCustom("external_id") and account.getCustom("external_id") != '':
        external_id = account.getCustom("external_id")

    arn = ARN_PREFIX + ':iam::' + account.identifier + ':role/' + role_name
    assume_role_kwargs = {
        'RoleArn': arn,
        'RoleSessionName': 'secmonkey'
    }
    if external_id:
        assume_role_kwargs['ExternalId'] = external_id

    role = sts.assume_role(**assume_role_kwargs)

    session = boto3.Session(
        aws_access_key_id=role['Credentials']['AccessKeyId'],
        aws_secret_access_key=role['Credentials']['SecretAccessKey'],
        aws_session_token=role['Credentials']['SessionToken']
    )
    return role, session.get_available_regions(service_name, partition_name=ARN_PARTITION)
