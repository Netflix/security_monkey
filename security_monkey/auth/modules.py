import itertools

from flask import request, abort, _app_ctx_stack, redirect
from flask_security.core import AnonymousUser
from security_monkey.datastore import User

try:
    from flask_login import current_user
except ImportError:
    current_user = None

from .models import RBACRole, RBACUserMixin

from . import anonymous

from flask import Response
import json


class AccessControlList(object):
    """
    This class record rules for access controling.
    """

    def __init__(self):
        self._allowed = []
        self._exempt = []
        self.seted = False

    def allow(self, role, method, resource, with_children=True):
        """Add allowing rules.

        :param role: Role of this rule.
        :param method: Method to allow in rule, include GET, POST, PUT etc.
        :param resource: Resource also view function.
        :param with_children: Allow role's children in rule as well
                              if with_children is `True`
        """

        if with_children:
            for r in role.get_children():
                permission = (r.name, method, resource)
                if permission not in self._allowed:
                    self._allowed.append(permission)
        permission = (role.name, method, resource)
        if permission not in self._allowed:
            self._allowed.append(permission)

    def exempt(self, view_func):
        """Exempt a view function from being checked permission

        :param view_func: The view function exempt from checking.
        """
        if not view_func in self._exempt:
            self._exempt.append(view_func)

    def is_allowed(self, role, method, resource):
        """Check whether role is allowed to access resource

        :param role: Role to be checked.
        :param method: Method to be checked.
        :param resource: View function to be checked.
        """
        return (role, method, resource) in self._allowed

    def is_exempt(self, view_func):
        """Return whether view_func is exempted.

        :param view_func: View function to be checked.
        """
        return view_func in self._exempt


class _RBACState(object):
    """Records configuration for Flask-RBAC"""
    def __init__(self, rbac, app):
        self.rbac = rbac
        self.app = app


class RBAC(object):
    """
    This class implements role-based access control module in Flask.
    There are two way to initialize Flask-RBAC::

        app = Flask(__name__)
        rbac = RBAC(app)

    :param app: the Flask object
    """

    _role_model = RBACRole
    _user_model = RBACUserMixin

    def __init__(self, app):
        self.acl = AccessControlList()
        self.before_acl = []

        self.app = app
        self.init_app(app)

    def init_app(self, app):
        # Add (RBAC, app) to flask extensions.
        # Add hook to authenticate permission before request.

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['rbac'] = _RBACState(self, app)

        self.acl.allow(anonymous, 'GET', app.view_functions['static'].__name__)
        app.before_first_request(self._setup_acl)
        app.before_request(self._authenticate)

    def has_permission(self, method, endpoint, user=None):
        """Return whether the current user can access the resource.
        Example::

            @app.route('/some_url', methods=['GET', 'POST'])
            @rbac.allow(['anonymous'], ['GET'])
            def a_view_func():
                return Response('Blah Blah...')

        If you are not logged.

        `rbac.has_permission('GET', 'a_view_func')` return True.
        `rbac.has_permission('POST', 'a_view_func')` return False.

        :param method: The method wait to check.
        :param endpoint: The application endpoint.
        :param user: user who you need to check. Current user by default.
        """
        app = self.get_app()
        _user = user or current_user
        roles = _user.get_roles()
        view_func = app.view_functions[endpoint]
        return self._check_permission(roles, method, view_func)

    def check_perm(self, role, method, callback=None):
        def decorator(view_func):
            if not self._check_permission([role], method, view_func):
                if callable(callback):
                    callback()
                else:
                    self._deny_hook()
            return view_func
        return decorator

    def allow(self, roles, methods, with_children=True):
        """Decorator: allow roles to access the view func with it.

        :param roles: List, each name of roles. Please note that,
                      `anonymous` is refered to anonymous.
                      If you add `anonymous` to the rule,
                      everyone can access the resource,
                      unless you deny other roles.
        :param methods: List, each name of methods.
                        methods is valid in ['GET', 'POST', 'PUT', 'DELETE']
        :param with_children: Whether allow children of roles as well.
                              True by default.
        """
        def decorator(view_func):
            _methods = [m.upper() for m in methods]
            for r, m, v in itertools.product(roles, _methods, [view_func.__name__]):
                self.before_acl.append((r, m, v, with_children))
            return view_func
        return decorator

    def exempt(self, view_func):
        """
        Decorator function
        Exempt a view function from being checked permission.
        """
        self.acl.exempt(view_func.__name__)
        return view_func

    def get_app(self, reference_app=None):
        """
        Helper to look up an app.
        """
        if reference_app is not None:
            return reference_app
        if self.app is not None:
            return self.app
        ctx = _app_ctx_stack.top
        if ctx is not None:
            return ctx.app
        raise RuntimeError('application not registered on rbac '
                           'instance and no application bound '
                           'to current context')

    def _authenticate(self):
        app = self.get_app()
        assert app, "Please initialize your application into Flask-RBAC."
        assert self._role_model, "Please set role model before authenticate."
        assert self._user_model, "Please set user model before authenticate."
        user = current_user
        if not isinstance(user._get_current_object(), self._user_model) and not isinstance(user._get_current_object(), AnonymousUser):
            raise TypeError(
                "%s is not an instance of %s" %
                (user, self._user_model.__class__))

        endpoint = request.endpoint
        resource = app.view_functions.get(endpoint, None)

        if not resource:
            abort(404)

        method = request.method
        if not hasattr(user, 'get_roles'):
            roles = [anonymous]
        else:
            roles = user.get_roles()

        permit = self._check_permission(roles, method, resource)
        if not permit:
            return self._deny_hook(resource=resource)

    def _check_permission(self, roles, method, resource):

        resource = resource.__name__
        if self.acl.is_exempt(resource):
            return True

        if not self.acl.seted:
            self._setup_acl()

        _roles = set()
        _methods = {'*', method}
        _resources = {None, resource}

        _roles.add(anonymous)

        _roles.update(roles)

        for r, m, res in itertools.product(_roles, _methods, _resources):
            if self.acl.is_allowed(r.name, m, res):
                return True

        return False

    def _deny_hook(self, resource=None):
        app = self.get_app()
        if current_user.is_authenticated:
            status = 403
        else:
            status = 401
        #abort(status)

        if app.config.get('FRONTED_BY_NGINX'):
                url = "https://{}:{}{}".format(app.config.get('FQDN'), app.config.get('NGINX_PORT'), '/login')
        else:
                url = "http://{}:{}{}".format(app.config.get('FQDN'), app.config.get('API_PORT'), '/login')
        if current_user.is_authenticated:
            auth_dict = {
                "authenticated": True,
                "user": current_user.email,
                "roles": current_user.role,
            }
        else:
            auth_dict = {
                "authenticated": False,
                "user": None,
                "url": url
            }

        return Response(response=json.dumps({"auth": auth_dict}), status=status, mimetype="application/json")


    def _setup_acl(self):
        for rn, method, resource, with_children in self.before_acl:
            role = self._role_model.get_by_name(rn)
            self.acl.allow(role, method, resource, with_children)
        self.acl.seted = True
