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
.. module: security_monkey.watchers.route53
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Alex Cline <alex.cline@gmail.com> @alex.cline

"""

from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.decorators import record_exception
from security_monkey.decorators import iter_account_region
from security_monkey import app

from cloudaux.aws.route53 import list_hosted_zones
from cloudaux.aws.route53 import list_resource_record_sets


class Route53(Watcher):
    index = 'route53'
    i_am_singular = 'Route53 Zone'
    i_am_plural = 'Route53 Zones'
    i_have_singular = 'Record Set'
    i_have_plural = 'Record Sets'

    def __init__(self, accounts=None, debug=False):
        super(Route53, self).__init__(accounts=accounts, debug=debug)

    @record_exception(source="route53-watcher")
    def list_hosted_zones(self, **kwargs):
        zones = list_hosted_zones(**kwargs)
        return [zone for zone in zones if not self.check_ignore_list(zone.get('Name', ''))]

    @record_exception(source="route53-watcher")
    def list_resource_record_sets(self, **kwargs):
        record_sets = list_resource_record_sets(**kwargs)
        return [record for record in record_sets if not self.check_ignore_list(record.get('Name', ''))]

    @record_exception(source="route53-watcher")
    def process_item(self, **kwargs):
        zone = kwargs['zone']
        record = kwargs['record']
        records = record.get('ResourceRecords', [])
        records = [r.get('Value') for r in records]
        record_name = record.get('Name', '')

        config = {
            'zonename': zone.get('Name'),
            'zoneid':   zone.get('Id'),
            'zoneprivate': zone.get('Config', {}).get('PrivateZone', 'Unknown'),
            'name':     record_name,
            'type':     record.get('Type'),
            'records':  records,
            'ttl':      record.get('TTL'),
        }

        print(config)

        return Route53Record(account=kwargs['account_name'], name=record_name, config=dict(config), source_watcher=self)

    def slurp(self):
        """
        :returns: item_list - list of Route53 zones.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception
        """
        self.prep_for_slurp()

        @iter_account_region(index=self.index, accounts=self.accounts, exception_record_region='universal')
        def slurp_items(**kwargs):
            app.logger.debug("Checking {}/{}".format(self.index, kwargs['account_name']))
            item_list = []

            zones = self.list_hosted_zones(**kwargs)
            if not zones:
                return item_list, kwargs['exception_map']
            

            app.logger.debug('Slurped {len_zones} {plural} from {account}.'.format(
                len_zones=len(zones),
                plural=self.i_am_plural,
                account=kwargs['account_name']))

            for zone in zones:
                record_sets = self.list_resource_record_sets(Id=zone['Id'], **kwargs)
                if not record_sets:
                    continue

                app.logger.debug("Slurped %s %s within %s %s (%s) from %s" %
                    (len(record_sets), self.i_have_plural, self.i_am_singular, zone['Name'], zone['Id'],
                     kwargs['account_name']))

                try:
                    for record in record_sets:
                        item = self.process_item(name=record['Name'], record=record, zone=zone, **kwargs)
                        item_list.append(item)
                except Exception as e:
                    raise

            return item_list, kwargs['exception_map']

        return slurp_items()


class Route53Record(ChangeItem):
    def __init__(self, account=None, name=None, config=None, source_watcher=None):
        super(Route53Record, self).__init__(
            index=Route53.index,
            region='universal',
            account=account,
            name=name,
            new_config=config if config else {},
            source_watcher=source_watcher)
