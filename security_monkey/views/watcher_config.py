#     Copyright 2016 Bridgewater Associates
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
"""
.. module: security_monkey.views.watcher_config
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from six import text_type

from security_monkey.views import AuthenticatedService
from security_monkey.datastore import WatcherConfig, Item, Technology
from security_monkey.watcher import watcher_registry
from security_monkey.views import WATCHER_CONFIG_FIELDS
from security_monkey import rbac, db

from flask_restful import marshal, reqparse


class WatcherConfigGetList(AuthenticatedService):
    decorators = [
        rbac.allow(["Admin"], ["GET"]),
    ]

    def __init__(self):
        super(WatcherConfigGetList, self).__init__()
        self.reqparse = reqparse.RequestParser()

    def get(self):
        self.reqparse.add_argument('count', type=int, default=30, location='args')
        self.reqparse.add_argument('page', type=int, default=1, location='args')

        args = self.reqparse.parse_args()
        page = args.pop('page', None)
        count = args.pop('count', None)

        configs = []
        all_keys = list(watcher_registry.keys())
        all_keys.sort()

        start_index = (page - 1) * count
        keys = all_keys[start_index:start_index + count]

        for key in keys:
            watcher_class = watcher_registry[key]
            config = WatcherConfig.query.filter(WatcherConfig.index == watcher_class.index).first()
            if config is None:
                config = WatcherConfig(id=0,
                                       index=watcher_class.index,
                                       interval=watcher_class.interval,
                                       active=True)

            configs.append(config)

        return_dict = {
            "page": page,
            "total": len(all_keys),
            "count": len(configs),
            "items": [marshal(item.__dict__, WATCHER_CONFIG_FIELDS) for item in configs],
            "auth": self.auth_dict
        }

        return return_dict, 200


class WatcherConfigPut(AuthenticatedService):
    decorators = [
        rbac.allow(["Admin"], ["Put"]),
    ]

    def __init__(self):
        super(WatcherConfigPut, self).__init__()

    def put(self, id):
        self.reqparse.add_argument('index', required=True, type=text_type, location='json')
        self.reqparse.add_argument('interval', required=True, type=int, location='json')
        self.reqparse.add_argument('active', required=True, type=bool, location='json')
        self.reqparse.add_argument('remove_items', required=False, type=bool, location='json')
        args = self.reqparse.parse_args()
        index = args['index']
        interval = args['interval']
        active = args['active']
        remove_items = args.get('remove_items', False)

        if id > 0:
            config = WatcherConfig.query.filter(WatcherConfig.id == id).first()
            config.interval = interval
            config.active = active
        else:
            config = WatcherConfig(index=index, interval=interval, active=active)

        db.session.add(config)
        db.session.commit()

        if active is False and remove_items is True:
            results = Item.query.join((Technology, Item.tech_id == Technology.id)) \
                                      .filter(Technology.name == index).all()

            for item in results:
                db.session.delete(item)
            db.session.commit()

        marshaled_dict = {
            'auth': self.auth_dict
        }

        return marshaled_dict, 200
