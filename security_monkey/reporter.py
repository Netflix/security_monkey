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
from security_monkey.account_manager import get_account_by_name
from security_monkey import app, db
from security_monkey.datastore import store_exception

import time


class Reporter(object):
    """Sets up all watchers and auditors and the alerters"""

    def __init__(self, account=None, debug=False):
        self.all_monitors = all_monitors(account, debug)
        self.account_alerter = Alerter(watchers_auditors=self.all_monitors, account=account)

    def run(self, account, interval=None):
        """Starts the process of watchers -> auditors -> alerters """
        app.logger.info("Starting work on account {}.".format(account))
        time1 = time.time()
        mons = self.get_monitors_to_run(account, interval)
        watchers_with_changes = set()

        for monitor in mons:
            app.logger.info("Running slurp {} for {} ({} minutes interval)".format(monitor.watcher.i_am_singular, account, interval))
            (items, exception_map) = monitor.watcher.slurp()
            monitor.watcher.find_changes(items, exception_map)
            if (len(monitor.watcher.created_items) > 0) or (len(monitor.watcher.changed_items) > 0):
                watchers_with_changes.add(monitor.watcher.index)
            monitor.watcher.save()

        db_account = get_account_by_name(account)

        for monitor in self.all_monitors:
            for auditor in monitor.auditors:
                if auditor.applies_to_account(db_account):
                    items_to_audit = self.get_items_to_audit(monitor.watcher, auditor, watchers_with_changes)
                    app.logger.info("Running audit {} for {}".format(
                                    monitor.watcher.index,
                                    account))

                    try:
                        auditor.audit_these_objects(items_to_audit)
                        auditor.save_issues()
                    except Exception as e:
                        store_exception('reporter-run-auditor', (auditor.index, account), e)
                        continue

        time2 = time.time()
        app.logger.info('Run Account %s took %0.1f s' % (account, (time2-time1)))

        self.account_alerter.report()

        db.session.close()

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
