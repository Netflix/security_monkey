from six import text_type

from security_monkey.auth.models import RBACRole

from security_monkey.views import AuthenticatedService
from security_monkey.views import USER_FIELDS
from security_monkey.datastore import User
from security_monkey.datastore import Role
from security_monkey import db, rbac

from flask_restful import marshal, reqparse
from flask_login import current_user

import json


class UserList(AuthenticatedService):
    decorators = [
        rbac.allow(["Admin"], ["GET"])
    ]

    def __init__(self):
        super(UserList, self).__init__()
        self.reqparse = reqparse.RequestParser()

    def get(self):
        """
            .. http:get:: /api/1/users

            Get a list of users, checking that the requester is an admin.

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/users HTTP/1.1
                Host: example.com
                Accept: application/json

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "auth": {
                        "authenticated": true,
                        "administrator": true,
                        "user": "user@example.com"
                    },
                    "users": [
                        {
                            "active": true,
                            "email": "john@example.com",
                            "id": "15",
                            "roles": [
                                1,
                                2,
                                3,
                                6,
                                17,
                                21,
                                22
                            ]
                        }
                    ]
                }

            :statuscode 200: no error
            :statuscode 401: Authentication Error. Please ensure you have administrator rights.
        """

        self.reqparse.add_argument('count', type=int, default=30, location='args')
        self.reqparse.add_argument('page', type=int, default=1, location='args')
        self.reqparse.add_argument('order_by', type=str, default=None, location='args')
        self.reqparse.add_argument('order_dir', type=str, default='desc', location='args')

        args = self.reqparse.parse_args()
        page = args.pop('page', None)
        count = args.pop('count', None)
        order_by = args.pop('order_by', None)
        order_dir = args.pop('order_dir', None)

        SENSITIVE_FIELDS = ['password']

        query = User.query
        if order_by and hasattr(User, order_by) and order_by not in SENSITIVE_FIELDS:
            if order_dir.lower() == 'asc':
                query = query.order_by(getattr(User, order_by).asc())
            else:
                query = query.order_by(getattr(User, order_by).desc())

        results = query.paginate(page, count)

        return_dict = {
            "page": results.page,
            "total": results.total,
            "count": len(results.items),
            "users": [marshal(user.__dict__, USER_FIELDS) for user in results.items],
            "auth": self.auth_dict
        }

        return return_dict, 200


class UserDetail(AuthenticatedService):
    decorators = [
        rbac.allow(["Admin"], ["PUT", "DELETE"])
    ]

    def delete(self, user_id):
        """
            .. http:delete:: /api/1/users/<int:user_id>

            Change the settings for the current user.

            **Example Request**:

            .. sourcecode:: http

                DELETE /api/1/users/15 HTTP/1.1
                Host: example.com
                Accept: application/json

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {}

            :statuscode 200: no error
            :statuscode 401: Authentication Error. Please Login.
            :statuscode 403: Cannot modify own user account.
            :statuscode 404: User entry with the given ID not found.
        """

        if user_id == current_user.id:
            return {"status": "Cannot modify own user account."},  403

        user = User.query.filter(User.id == user_id).first()

        if not user:
            return {"status": "User entry with the given ID not found."}, 404

        db.session.delete(user)
        db.session.commit()

        return_dict = {
            "auth": self.auth_dict
        }

        return return_dict, 202

    def put(self, user_id):
        """
            .. http:put:: /api/1/users/<int:user_id>

            Change the settings for the current user.

            **Example Request**:

            .. sourcecode:: http

                PUT /api/1/users/15 HTTP/1.1
                Host: example.com
                Accept: application/json

                {
                    "user": {
                        "active": true,
                        "email": "john@example.com",
                        "id": "15",
                        "roles": [
                            1,
                            2,
                            3,
                            6,
                            17,
                            21,
                            22
                        ]
                    }
                }

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {}

            :statuscode 200: no error
            :statuscode 401: Authentication Error. Please Login.
            :statuscode 403: Cannot modify own user account.
            :statuscode 404: User entry with the given ID not found.
        """

        self.reqparse.add_argument('id', required=True, location='json', type=int)
        self.reqparse.add_argument('email', required=True, location='json', type=text_type)
        self.reqparse.add_argument('active', required=True, location='json', type=bool)
        self.reqparse.add_argument('role_id', required=True, location='json', type=str)
        args = self.reqparse.parse_args()

        if user_id != args['id']:
            return {"status": "User ID cannot be modified."},  403

        if user_id == current_user.id:
            return {"status": "Cannot modify own user account."},  403

        email = args.get('email')
        active = args.get('active')
        role_id = args.get('role_id')

        user = User.query.filter(User.id == user_id).first()

        if not user:
            return {"status": "User entry with the given ID not found."}, 404

        # Don't blindly trust new email addresses
        # user.email = email
        user.active = active
        if role_id in RBACRole.roles:
            user.role = role_id
        else:
            return {"status": "Specified Role not found."}, 404
        db.session.add(user)
        db.session.commit()

        return_dict = {
            "auth": self.auth_dict
        }

        return return_dict, 202


class Roles(AuthenticatedService):
    decorators = [
        rbac.allow(["Admin"], ["GET"])
    ]

    def get(self):
        """
            .. http:get:: /api/1/roles

            Get a list of roles, checking that the requester is an admin.

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/roles HTTP/1.1
                Host: example.com
                Accept: application/json

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "auth": {
                        "authenticated": true,
                        "administrator": true,
                        "user": "user@example.com"
                    },
                    "roles": [
                        {
                            "id": 1,
                            "name": "admin",
                            "description": "Administrators"
                        }
                    ]
                }

            :statuscode 200: no error
            :statuscode 401: Authentication Error. Please ensure you have administrator rights.
        """

        return_dict = {
            "auth": self.auth_dict
        }

        roles = []

        for name in RBACRole.roles:
            roles.append({"name": RBACRole.roles[name].name})

        return_dict["roles"] = roles

        return return_dict, 200
