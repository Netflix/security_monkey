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
.. module: security_monkey.reporter
    :platform: Unix
    :synopsis: Runs all change watchers and auditors and uses the alerter
    to send emails for a specific account.

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

from security_monkey.alerter import Alerter
from security_monkey.monitors import all_monitors
from security_monkey import app


class Reporter(object):
    """Sets up all watchers and auditors and the alerters"""

    def __init__(self, account=None, debug=False):
        self.all_monitors = all_monitors(account, debug)
        self.account_alerter = Alerter(watchers_auditors=self.all_monitors, account=account)

    def get_monitors_to_run(self, account, interval=None):
        """
        Return a list of (watcher, auditor) enabled for a specific account,
        optionally filtered by interval time
        """
        mons = []
        if interval:
            for monitor in self.all_monitors:
                if monitor.watcher and interval == monitor.watcher.get_interval():
                    mons.append(monitor)
        else:
            mons = self.all_monitors
        return mons

    def get_intervals(self, account):
        """ Returns current intervals for watchers """
        buckets = []
        for monitor in self.all_monitors:
            if monitor.watcher:
                interval = monitor.watcher.get_interval()
                if interval not in buckets:
                    buckets.append(interval)
        return buckets

    def get_items_to_audit(self, watcher, auditor, watchers_with_changes):
        """
        Returns the items that have changed if there are no changes in dependencies,
        otherwise returns all slurped items for reauditing
        """
        watcher.full_audit_list = None
        if auditor.support_watcher_indexes:
            for support_watcher_index in auditor.support_watcher_indexes:
                if support_watcher_index in watchers_with_changes:
                    app.logger.debug("Upstream watcher changed {}. reauditing {}".format(
                                     support_watcher_index, watcher.index))

                    watcher.full_audit_list = auditor.read_previous_items()
        if auditor.support_auditor_indexes:
            for support_auditor_index in auditor.support_auditor_indexes:
                if support_auditor_index in watchers_with_changes:
                    app.logger.debug("Upstream auditor changed {}. reauditing {}".format(
                                     support_auditor_index, watcher.index))
                    watcher.full_audit_list = auditor.read_previous_items()

        if watcher.full_audit_list:
            return watcher.full_audit_list

        return [item for item in watcher.created_items + watcher.changed_items]
