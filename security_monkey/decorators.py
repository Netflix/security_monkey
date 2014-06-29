"""
.. module: decorators
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
