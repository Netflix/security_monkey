"""
.. module: security_monkey.tests.utilities.test_sync_network
    :platform: Unix
.. version:: $$VERSION$$
.. moduleauthor::  Mark Ignacio <mignacio@fb.com>
"""
import json
import tempfile
import sys
from io import BytesIO

from security_monkey.datastore import NetworkWhitelistEntry
from security_monkey.manage import manager
from security_monkey.tests import SecurityMonkeyTestCase

import boto3
from moto import mock_s3


class SyncNetworksTestCase(SecurityMonkeyTestCase):
    TEST_NETWORKS = {
        'network-un': '23.246.2.0/24', 
        'network-deux': '2607:fb10:70b0::/44',
    }
    TEST_NETWORKS_ENCODED = json.dumps(TEST_NETWORKS).encode('utf-8')


    def test_add_whitelist_entries(self):
        self.__sync_networks(self.TEST_NETWORKS_ENCODED)
        for name, cidr in self.TEST_NETWORKS.items():
            entry = NetworkWhitelistEntry.query.filter(
                NetworkWhitelistEntry.name == name
            ).first()
            assert entry is not None
            assert entry.cidr == cidr

    def test_add_whitelist_entries_with_s3(self):
        # this test exhausts the code path for the s3.get_object() call. The
        # tests below are agnostic to storage, so it's just more convenient
        # to use local files.
        mock_s3().start()
        s3 = boto3.client('s3')
        s3.create_bucket(Bucket='testBucket')
        s3.put_object(
            Bucket='testBucket',
            Key='networks.json',
            Body=json.dumps(self.TEST_NETWORKS).encode('utf-8'),
        )
        manager.handle(
            'manage.py',
            ['sync_networks', '-i', 'networks.json', '-b', 'testBucket'],
        )
        #mock_s3().stop()
        for name, cidr in list(self.TEST_NETWORKS.items()):
            entry = NetworkWhitelistEntry.query.filter(
                NetworkWhitelistEntry.name == name
            ).first()
            assert entry is not None
            assert entry.cidr == cidr

    def test_update_whitelist_entry(self):
        self.__sync_networks(self.TEST_NETWORKS_ENCODED)
        modified_networks = self.TEST_NETWORKS
        modified_networks['network-un'] = '23.246.2.0/24'
        modified_networks_encoded=json.dumps(modified_networks).encode('utf-8')
        self.__sync_networks(modified_networks_encoded)
        modified = NetworkWhitelistEntry.query.filter(
            NetworkWhitelistEntry.name == 'network-un'
        )
        assert modified.count() == 1
        entry = modified.first()
        assert entry is not None
        assert entry.cidr == '23.246.2.0/24'

    def test_update_whitelist_authoritatively(self):
        self.__sync_networks(self.TEST_NETWORKS_ENCODED, ['-a'])
        # adding one and removing one should do it.
        modified_networks = self.TEST_NETWORKS
        del modified_networks['network-deux']
        modified_networks['network-trois'] = '2a00:86c0:ff0a::/48'
        modified_networks_encoded=json.dumps(modified_networks).encode('utf-8')
        self.__sync_networks(modified_networks_encoded, ['-a'])
        assert NetworkWhitelistEntry.query.filter(
            NetworkWhitelistEntry.name == 'network-deux'
        ).count() == 0
        assert NetworkWhitelistEntry.query.filter(
            NetworkWhitelistEntry.name == 'network-trois'
        ).count() == 1

    @staticmethod
    def __sync_networks(networks, additional_args=None):
        if additional_args is None:
            additional_args = []
        with tempfile.NamedTemporaryFile() as tfile:
            tfile.write(networks)
            tfile.seek(0)
            manager.handle(
                'manage.py',
                ['sync_networks', '-i', tfile.name] + additional_args,
            )

