"""
.. module: security_monkey.decorators
    :synopsis: Defines decorators allowing for credentialed CORS access.

.. version:: $$VERSION$$
.. moduleauthor:: Armin Ronacher (http://flask.pocoo.org/snippets/56/)

"""

from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper


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


from functools import wraps
import boto3, boto, botocore
import dateutil.tz
import datetime
import time

CACHE = {}


def rate_limited(max_attempts=None, max_delay=4):
    def decorator(f):
        metadata = {
            'count': 0,
            'delay': 0
        }

        @wraps(f)
        def decorated_function(*args, **kwargs):
            def increase_delay(e):
                print "[rl]"
                if metadata['delay'] == 0:
                    metadata['delay'] = 1
                elif metadata['delay'] < max_delay:
                    metadata['delay'] *= 2

                if max_attempts and metadata['count'] > max_attempts:
                    raise e

            metadata['count'] = 0
            while True:
                metadata['count'] += 1
                if metadata['delay'] > 0:
                    time.sleep(metadata['delay'])
                try:
                    retval = f(*args, **kwargs)
                    metadata['delay'] = 0
                    return retval
                except botocore.exceptions.ClientError as e:
                    if not e.response["Error"]["Code"] == "Throttling":
                        raise e
                    increase_delay(e)
                except boto.exception.BotoServerError as e:
                    if not e.error_code == 'Throttling':
                        raise e
                    increase_delay(e)
        return decorated_function
    return decorator


def _client(service, region, role):
    return boto3.client(
        service,
        region_name=region,
        aws_access_key_id=role['Credentials']['AccessKeyId'],
        aws_secret_access_key=role['Credentials']['SecretAccessKey'],
        aws_session_token=role['Credentials']['SessionToken']
    )


def _resource(service, region, role):
    return boto3.resource(
        service,
        region_name=region,
        aws_access_key_id=role['Credentials']['AccessKeyId'],
        aws_secret_access_key=role['Credentials']['SecretAccessKey'],
        aws_session_token=role['Credentials']['SessionToken']
    )


# @rate_limited()
def sts_conn(service, service_type='client', future_expiration_minutes=15):
    def decorator(f):
        @wraps(f)
        def stsdecorated_function(*args, **kwargs):

            key = (
                kwargs.get('account_number'),
                kwargs.get('assume_role'),
                kwargs.get('session_name'),
                kwargs.get('region', 'us-east-1'),
                service_type,
                service
            )

            if key in CACHE:
                (val, exp) = CACHE[key]
                now = datetime.datetime.now(dateutil.tz.tzutc()) \
                    + datetime.timedelta(minutes=future_expiration_minutes)
                if exp > now:
                    print "[c]"  # ,key
                    kwargs[service_type] = val
                    return f(*args, **kwargs)
                else:
                    del CACHE[key]

            print '[n]'
            sts = boto3.client('sts')
            arn = 'arn:aws:iam::{0}:role/{1}'.format(
                kwargs.pop('account_number'),
                kwargs.pop('assume_role')
            )
            role = sts.assume_role(RoleArn=arn, RoleSessionName=kwargs.pop('session_name', 'security_monkey'))

            if service_type == 'client':
                kwargs[service_type] = _client(service, kwargs.pop('region', 'us-east-1'), role)
            elif service_type == 'resource':
                kwargs[service_type] = _resource(service, kwargs.pop('region', 'us-east-1'), role)

            CACHE[key] = (kwargs[service_type], role['Credentials']['Expiration'])

            return f(*args, **kwargs)

        return stsdecorated_function
    return decorator
