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

from security_monkey.views import AuthenticatedService

from security_monkey import rbac, app

from flask import request
from flask_restful import marshal, reqparse
from flask_login import current_user

import json
import security_monkey.plugins.splunk_alerter.splunk_alerter_exceptions as SplkEx
from security_monkey.plugins.splunk_alerter.splunk_alerter_plugin import SPLUNK_ALERTER_FIELDS
from security_monkey.plugins.splunk_alerter.splunk_alerter import SplunkHECAlerter


class SplunkAlerterGetPutDelete(AuthenticatedService):
    decorators = [
        rbac.allow(["View"], ["GET"]),
        rbac.allow(["Admin"], ["PUT", "DELETE"])
    ]

    def __init__(self):
        from security_monkey.plugins.splunk_alerter.splunk_alerter_plugin import SplunkAlerterPlugin
        self.instance = SplunkAlerterPlugin()
        self.reqparse = reqparse.RequestParser()
        super(SplunkAlerterGetPutDelete, self).__init__()

    def get(self, alerter_id):
        alerter = self.instance.get_alerter(alerter_id)
        if not alerter:
            return {'status': 'error. Alerter ID not found.'}, 404

        alerter_marshaled = marshal(alerter.to_dict(), SPLUNK_ALERTER_FIELDS)
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
        sourcetype = args['sourcetype']
        source = args['source']

        if args['active'] is None:
            active = False
        else:
            active = args['active']

        if args['log_config'] is None:
            log_config = False
        else:
            log_config = args['log_config']

        try:
            app.logger.warn(args)
            alerter = self.instance.edit(alerter_id, host, port, token, active, log_config, sourcetype, source)
        except SplkEx.SplunkAlerterExists as _:
            return {'status': 'error. Alerter name exists.'}, 409
        except SplkEx.SplunkAlerterFieldFormatError as _:
            return {'status': 'error. Alerter {} field validation error.'.format(_.field)}, 400
        if not alerter:
            return {'status': 'error. Alerter ID not found.'}, 404

        marshaled_alerter = marshal(alerter.to_dict(), SPLUNK_ALERTER_FIELDS)

        app.logger.warn(marshaled_alerter)
        marshaled_alerter['auth'] = self.auth_dict

        return marshaled_alerter, 200

    def delete(self, alerter_id):
        self.instance.delete_alerter(alerter_id)
        return {'status': 'deleted'}, 202


class SplunkAlerterPostList(AuthenticatedService):
    decorators = [
        rbac.allow(["View"], ["GET"]),
        rbac.allow(["Admin"], ["POST"])
    ]

    def __init__(self):
        super(SplunkAlerterPostList, self).__init__()
        from security_monkey.plugins.splunk_alerter.splunk_alerter_plugin import SplunkAlerterPlugin
        self.instance = SplunkAlerterPlugin()
        self.reqparse = reqparse.RequestParser()

    def post(self):
        args = json.loads(request.json)
        host = args['host']
        port = int(args['port'])
        token = args['token']
        sourcetype = args['sourcetype']
        source = args['source']
        if args['active'] is None:
            active = False
        else:
            active = args['active']

        if args['log_config'] is None:
            log_config = False
        else:
            log_config = args['log_config']

        try:
            alerter = self.instance.create(host, port, token, active, log_config, sourcetype, source)
        except SplkEx.SplunkAlerterExists:
            return {'status': 'error. Alerter host:port exists.'}, 409
        except SplkEx.SplunkAlerterFieldFormatError as _:
            return {'status': 'error. Alerter {} field validation error.'.format(_.field)}, 400

        marshaled_alerter = marshal(alerter.to_dict(), SPLUNK_ALERTER_FIELDS)
        marshaled_alerter['auth'] = self.auth_dict

        return marshaled_alerter, 200

    def get(self):
        self.reqparse.add_argument('count', type=int, default=30, location='args')
        self.reqparse.add_argument('page', type=int, default=1, location='args')
        self.reqparse.add_argument('order_by', type=str, default=None, location='args')
        self.reqparse.add_argument('order_dir', type=str, default='desc', location='args')
        self.reqparse.add_argument('active', type=str, default=None, location='args')
        self.reqparse.add_argument('log_config', type=str, default=None, location='args')
        self.reqparse.add_argument('sourcetype', type=str, default=None, location='args')
        self.reqparse.add_argument('source', type=str, default=None, location='args')

        args = self.reqparse.parse_args()
        page = args.pop('page', None)
        count = args.pop('count', None)
        order_by = args.pop('order_by', None)
        order_dir = args.pop('order_dir', None)
        for k, v in args.items():
            if not v:
                del args[k]
        query = self.instance.get_alerters()
        if 'active' in args:
            active = args['active'].lower() == "true"
            query = self.instance.get_active_alerter(active)

        if 'log_config' in args:
            log_config = args['log_config'].lower() == "true"
            query = self.instance.get_alerter_with_log_config(log_config)

        if order_by in SPLUNK_ALERTER_FIELDS.keys():
            query.sort(key=lambda x: getattr(x, order_by))
        else:
            query.sort(key=lambda x: x.id)
        if query is not None:
            result = query[count * (page-1):count * page]
        else:
            result = []

        items = []
        for alerter in result:
            alerter_marshaled = marshal(alerter.to_dict(), SPLUNK_ALERTER_FIELDS)
            alerter_marshaled = dict(
                alerter_marshaled.items()
            )

            if current_user.role != "Admin":
                alerter_marshaled["token"] = None
            items.append(alerter_marshaled)

        marshaled_dict = {
            'total': len(result),
            'count': len(items),
            'page': page,
            'items': items,
            'auth': self.auth_dict
        }

        return marshaled_dict, 200


