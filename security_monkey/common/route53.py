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
"""
.. module:: route53
    :platform: Unix
    :synopsis: Module contains a useful Route53 class.
.. version:: @VERSION@
.. author:: Kevin Glisson (kglisson@netflix.com), Patrick Kelley (patrick@netflix.com) @monkeysecurity
"""

import os
import re
import boto
import boto.route53.record

from security_monkey import app


class Route53Service(object):
    """
        Class provides useful functions of manipulating Route53 records
    """
    def __init__(self, **kwargs):
        super(Route53Service, self).__init__(**kwargs)
        self.conn = boto.connect_route53()

        try:
            self.hostname = os.environ['EC2_PUBLIC_HOSTNAME']
        except KeyError:
            app.logger.warn("We cannot register a domain on non ec2 instances")

    def register(self, fqdn, exclusive=False, ttl=60, type='CNAME', regions=None):
        fqdn = fqdn.replace('_', '-')
        fqdn = re.sub(r'[^\w\-\.]', '', fqdn)
        app.logger.debug('route53: register fqdn: {}, hostname: {}'.format(fqdn, self.hostname))

        zone_id = self._get_zone_id(fqdn)

        if exclusive:
            app.logger.debug('route53: making fqdn: {} exclusive'.format(fqdn))

            rrsets = self.conn.get_all_rrsets(zone_id, type, name=fqdn)
            for rrset in rrsets:
                if rrset.name == fqdn + '.':
                    app.logger.debug('found fqdn to delete: {}'.format(rrset))

                    for rr in rrset.resource_records:
                        changes = boto.route53.record.ResourceRecordSets(self.conn, zone_id)
                        changes.add_change("DELETE", fqdn, type, ttl).add_value(rr)
                        changes.commit()

        changes = boto.route53.record.ResourceRecordSets(self.conn, zone_id)
        changes.add_change("CREATE", fqdn, type, ttl).add_value(self.hostname)
        changes.commit()

    def unregister(self, fqdn, ttl=60, type='CNAME'):
        # Unregister this fqdn
        fqdn = fqdn.replace('_', '-')
        fqdn = re.sub(r'[^\w\-\.]', '', fqdn)

        app.logger.debug('route53: unregister fqdn: {}, hostname: {}'.format(fqdn, self.hostname))

        zone_id = self._get_zone_id(fqdn)

        changes = boto.route53.record.ResourceRecordSets(self.conn, zone_id)
        changes.add_change("DELETE", fqdn, type, ttl).add_value(self.hostname)
        changes.commit()

    def _get_zone_id(self, domain):

        if domain[-1] != '.':
            domain += '.'

        result = self.conn.get_all_hosted_zones()
        hosted_zones = result['ListHostedZonesResponse']['HostedZones']

        while domain != '.':
            for zone in hosted_zones:
                app.logger.debug("{} {}".format(zone['Name'], domain))
                if zone['Name'] == domain:
                    return zone['Id'].replace('/hostedzone/', '')
            else:
                domain = domain[domain.find('.') + 1:]
        raise ZoneIDNotFound(domain)
