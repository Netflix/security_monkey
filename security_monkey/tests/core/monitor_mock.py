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
CURRENT_MONITORS = []


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


def build_mock_result(watcher_configs, auditor_configs):
    """
    Builds mock monitor results that can be used to override the results of the
    monitor methods.
    """
    del CURRENT_MONITORS[:]

    for config in watcher_configs:
        watcher = mock_watcher(config)

        auditors = []

        for config in auditor_configs:
            if config['index'] == watcher.index:
                auditors.append(mock_auditor(config))

        CURRENT_MONITORS.append(MockMonitor(watcher, auditors))


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


def mock_all_monitors(account_name, debug=False):
    return CURRENT_MONITORS


def mock_get_monitors(account_name, monitor_names, debug=False):
    monitors = []
    for monitor in CURRENT_MONITORS:
        if monitor.watcher.index in monitor_names:
            monitors.append(monitor)

    return monitors
