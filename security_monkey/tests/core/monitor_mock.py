#     Copyright 2017 Bridgewater Associates
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
.. module: security_monkey.tests.core.mock_monitor
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>

"""
from security_monkey.watcher import ChangeItem

from collections import defaultdict

RUNTIME_WATCHERS = defaultdict(list)
RUNTIME_AUDIT_COUNTS = defaultdict(list)
CURRENT_MONITOR_CONFIGS = {}


class MockMonitor(object):
    def __init__(self, watcher, auditors):
        self.watcher = watcher
        self.auditors = auditors
        self.batch_support = self.watcher.batched_size > 0


class MockRunnableWatcher(object):
    def __init__(self, index, interval):
        self.index = index
        self.interval = interval
        self.i_am_singular = index
        self.created_items = []
        self.deleted_items = []
        self.changed_items = []

        self.batched_size = 0
        self.done_slurping = True
        self.total_list = []
        self.batch_counter = 0

    def slurp(self):
        RUNTIME_WATCHERS[self.index].append(self)
        item_list = []
        exception_map = {}
        return item_list, exception_map

    def save(self):
        pass

    def get_interval(self):
        return self.interval

    def find_changes(self, current=[], exception_map={}):
        self.created_items.append(ChangeItem(index=self.index))

    def cleanup(self):
        del self.created_items[:]
        del self.deleted_items[:]
        del self.changed_items[:]


class MockRunnableAuditor(object):
    def __init__(self, index, support_auditor_indexes, support_watcher_indexes):
        self.index = index
        self.support_auditor_indexes = support_auditor_indexes
        self.support_watcher_indexes = support_watcher_indexes
        self.items = []

    def audit_objects(self):
        item_count = RUNTIME_AUDIT_COUNTS.get(self.index, 0)
        RUNTIME_AUDIT_COUNTS[self.index] = item_count + len(self.items)

    def save_issues(self):
        pass

    def applies_to_account(self, db_account):
        return True

    def read_previous_items(self):
        return [ChangeItem(index=self.index)]

    def cleanup(self):
        del self.items[:]


def build_mock_result(watcher_configs, auditor_configs):
    """
    Holds the configurations so that monitors can be generated. This is to
    mock monitor results that can be used to override the results of the
    monitor methods.
    """
    CURRENT_MONITOR_CONFIGS["watcher_configs"] = watcher_configs
    CURRENT_MONITOR_CONFIGS["auditor_configs"] = auditor_configs


def mock_all_monitors(account, debug):
    """
    This will generate the monitors based on the current monitor configs.
    Because of the mocking and the deletion of monitor watchers and auditors for memory saving,
    monitors need to be re-generated for the tests to succeed.
    :return:
    """
    monitors = []

    for config in CURRENT_MONITOR_CONFIGS["watcher_configs"]:
        watcher = mock_watcher(config)

        auditors = []

        for config in CURRENT_MONITOR_CONFIGS["auditor_configs"]:
            if config['index'] == watcher.index:
                auditors.append(mock_auditor(config))

        monitors.append(MockMonitor(watcher, auditors))

    return monitors


def mock_watcher(config):
    """
    Builds a mock watcher from a config dictionary like:
    {
        'index': 'index1',
        'interval: 15'
    }
    """
    return MockRunnableWatcher(config['index'], config['interval'])


def mock_auditor(config):
    """
    Builds a mock auditor from a config dictionary like:
    {
        'index': 'index1',
        'support_auditor_indexes': [],
        'support_watcher_indexes': ['index2']
    }
    """
    return MockRunnableAuditor(config['index'],
                               config['support_auditor_indexes'],
                               config['support_watcher_indexes'])


def mock_get_monitors(account_name, monitor_names, debug=False):
    monitors = []
    for monitor in mock_all_monitors(account_name, debug):
        if monitor.watcher.index in monitor_names:
            monitors.append(monitor)

    return monitors
