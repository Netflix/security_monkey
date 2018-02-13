#     Copyright 2014 Netflix, Inc.
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
from security_monkey.exceptions import SplunkAlerterExists, SplunkAlerterFieldFormatError
from security_monkey.views import AuthenticatedService
from security_monkey.views import SPLUNK_ALERTER_FIELDS
from security_monkey.datastore import SplunkAlerter
from security_monkey.alerters.splunk_alerter import SplunkHECAlerter
from security_monkey import db, rbac, app

from flask import request
from flask_restful import marshal, reqparse
from flask_login import current_user

import json

class SplunkAlerterGetPutDelete(AuthenticatedService):
    decorators = [
        rbac.allow(["View"], ["GET"]),
        rbac.allow(["Admin"], ["PUT", "DELETE"])
    ]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(SplunkAlerterGetPutDelete, self).__init__()

    def get(self, alerter_id):
        alerter = SplunkAlerter.query.filter(SplunkAlerter.id == alerter_id).first()
        if not alerter:
            return {'status': 'error. Alerter ID not found.'}, 404

        alerter_marshaled = marshal(alerter.__dict__, SPLUNK_ALERTER_FIELDS)
        if current_user.role != "Admin":
            alerter_marshaled["token"] = None
        alerter_marshaled = dict(
            alerter_marshaled.items()
        )
        alerter_marshaled['auth'] = self.auth_dict
        return alerter_marshaled, 200

    def put(self, alerter_id):
        args = json.loads(request.json)
        host = args['host']
        port = int(args['port'])
        token = args['token']
        if args['active'] is None:
            active = False
        else:
            active = args['active']

        alerter_manager = SplunkHECAlerter()

        try:
            app.logger.warn(args)
            alerter = alerter_manager.add(alerter_id, host, port, token, active)
        except SplunkAlerterExists as _:
            return {'status': 'error. Alerter name exists.'}, 409
        except SplunkAlerterFieldFormatError as _:
            return {'status': 'error. Alerter {} field validation error.'.format(_.field)}, 400
        if not alerter:
            return {'status': 'error. Alerter ID not found.'}, 404



        marshaled_alerter = marshal(alerter.__dict__, SPLUNK_ALERTER_FIELDS)

        app.logger.warn(marshaled_alerter)
        marshaled_alerter['auth'] = self.auth_dict

        return marshaled_alerter, 200

    def delete(self, alerter_id):
        alerter = SplunkAlerter.query.filter(SplunkAlerter.id == alerter_id).first()
        db.session.delete(alerter)
        db.session.commit()
        return {'status': 'deleted'}, 202


class SplunkAlerterPostList(AuthenticatedService):
    decorators = [
        rbac.allow(["View"], ["GET"]),
        rbac.allow(["Admin"], ["POST"])
    ]

    def __init__(self):
        super(SplunkAlerterPostList, self).__init__()
        self.reqparse = reqparse.RequestParser()

    def post(self):
        args = json.loads(request.json)
        host = args['host']
        port = int(args['port'])
        token = args['token']
        if args['active'] is None:
            active = False
        else:
            active = args['active']

        try:
            alerter_manager = SplunkHECAlerter()
            alerter = alerter_manager.create(host, port, token, active)

        except SplunkAlerterExists:
            return {'status': 'error. Alerter host:port exists.'}, 409
        except SplunkAlerterFieldFormatError as _:
            return {'status': 'error. Alerter {} field validation error.'.format(_.field)}, 400

        marshaled_alerter = marshal(alerter.__dict__, SPLUNK_ALERTER_FIELDS)
        marshaled_alerter['auth'] = self.auth_dict

        return marshaled_alerter, 200

    def get(self):
        self.reqparse.add_argument('count', type=int, default=30, location='args')
        self.reqparse.add_argument('page', type=int, default=1, location='args')
        self.reqparse.add_argument('order_by', type=str, default=None, location='args')
        self.reqparse.add_argument('order_dir', type=str, default='desc', location='args')
        self.reqparse.add_argument('active', type=str, default=None, location='args')

        args = self.reqparse.parse_args()
        page = args.pop('page', None)
        count = args.pop('count', None)
        order_by = args.pop('order_by', None)
        order_dir = args.pop('order_dir', None)
        for k, v in args.items():
            if not v:
                del args[k]

        query = SplunkAlerter.query
        if 'active' in args:
            active = args['active'].lower() == "true"
            query = query.filter(SplunkAlerter.active == active)

        if order_by and hasattr(SplunkAlerter, order_by):
            query = query.order_by(getattr(SplunkAlerter, order_by).desc())
        else:
            query = query.order_by(SplunkAlerter.id)

        result = query.paginate(page, count, error_out=False)

        items = []
        for alerter in result.items:
            alerter_marshaled = marshal(alerter.__dict__, SPLUNK_ALERTER_FIELDS)
            alerter_marshaled = dict(
                alerter_marshaled.items()
            )

            if current_user.role != "Admin":
                alerter_marshaled["token"] = None
            items.append(alerter_marshaled)

        marshaled_dict = {
            'total': result.total,
            'count': len(items),
            'page': result.page,
            'items': items,
            'auth': self.auth_dict
        }

        return marshaled_dict, 200
