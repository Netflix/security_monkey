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
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey import app


class Route53(Watcher):
    index = 'route53'
    i_am_singular = 'Route53 Zone'
    i_am_plural = 'Route53 Zones'
    i_have_singular = 'Record Set'
    i_have_plural = 'Record Sets'

    def __init__(self, accounts=None, debug=False):
        super(Route53, self).__init__(accounts=accounts, debug=debug)

    def record_sets_for_zone(self, conn, zone):
        all_record_sets = []
        marker = None
        while True:
            response = self.wrap_aws_rate_limited_call(
                conn.get_all_rrsets,
                zone
            )
            all_record_sets.extend(response)
            if response.is_truncated != u'true':
                break
        return all_record_sets

    def slurp(self):
        """
        :returns: item_list - list of Route53 zones.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()
        from security_monkey.common.sts_connect import connect
        item_list = []
        exception_map = {}
        for account in self.accounts:

            app.logger.debug("Checking {}/{}".format(self.index, account, 'universal'))
            all_zones = []

            try:
                route53 = connect(account, 'route53')

                zones = self.wrap_aws_rate_limited_call(
                    route53.get_zones
                )

            except Exception as e:
                exc = BotoConnectionIssue(str(e), self.index, account, None)
                self.slurp_exception((self.index, account, 'universal'), exc, exception_map)
                continue
            app.logger.debug("Found {} {}.".format(len(zones), self.i_am_plural))

            for zone in zones:
                if self.check_ignore_list(zone):
                    continue

                zone_info = self.wrap_aws_rate_limited_call(
                    route53.get_hosted_zone,
                    zone.id
                )
                record_sets = self.record_sets_for_zone(route53, zone.id)

                app.logger.debug("Slurped %s %s within %s %s (%s) from %s" %
                    (len(record_sets), self.i_have_plural, self.i_am_singular, zone.name, zone.id, account))

                for record in record_sets:
                    config = {
                        'zonename': zone.name,
                        'zoneid':   zone.id,
                        'zoneprivate': zone_info['GetHostedZoneResponse']['HostedZone']['Config']['PrivateZone'] == 'true',
                        'name':     record.name.decode('unicode-escape'),
                        'type':     record.type,
                        'records':  record.resource_records,
                        'ttl':      record.ttl,
                    }

                    item = Route53Record(account=account, name=record.name, config=dict(config))
                    item_list.append(item)

        return item_list, exception_map


class Route53Record(ChangeItem):
    def __init__(self, account=None, name=None, config={}):
        super(Route53Record, self).__init__(
            index=Route53.index,
            region='universal',
            account=account,
            name=name,
            new_config=config)
