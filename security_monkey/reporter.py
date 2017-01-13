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
from security_monkey import app, db

import time


class Reporter(object):
    """Sets up all watchers and auditors and the alerters"""

    def __init__(self, account=None, alert_accounts=None, debug=False):
        self.account_watchers = {}
        self.account_alerters = {}
        if not alert_accounts:
            alert_accounts = [account]

        self.account_watchers[account] = []
        for monitor in all_monitors(account, debug):
            self.account_watchers[account].append((monitor))

        if account in alert_accounts:
            self.account_alerters[account] = Alerter(watchers_auditors=self.account_watchers[account], account=account)

    def run(self, account, interval=None):
        """Starts the process of watchers -> auditors -> alerters -> watchers.save()"""
        app.logger.info("Starting work on account {}.".format(account))
        time1 = time.time()
        mons = self.get_watchauditors(account, interval)
        unique_watcher_results = self.slurp_unique_watchers(mons, account, interval)

        monitors_with_changes = set()
        for monitor in mons:
            slurped_watcher_results = unique_watcher_results.get(monitor.watcher.index)
            monitor.watcher.find_changes(slurped_watcher_results[0], slurped_watcher_results[1])
            if (len(monitor.watcher.created_items) > 0) or (len(monitor.watcher.changed_items) > 0):
                monitors_with_changes.add(monitor.watcher.index)
            monitor.watcher.save()

        for monitor in mons:
            for auditor in monitor.auditors:
                items_to_audit = self.get_items_to_audit(monitor, auditor, unique_watcher_results.get(monitor.watcher.index), monitors_with_changes)
                auditor.audit_these_objects(items_to_audit)
                auditor.save_issues()

            app.logger.info("Account {} is done with {}".format(account, monitor.watcher.i_am_singular))

        time2 = time.time()
        app.logger.info('Run Account %s took %0.1f s' % (account, (time2-time1)))

        if account in self.account_alerters:
            self.account_alerters[account].report()

        db.session.close()

    def get_watchauditors(self, account, interval=None):
        """
        Return a list of (watcher, auditor) enabled for a specific account,
        optionally filtered by interval time
        """
        mons = []
        if interval:
            for monitor in self.account_watchers[account]:
                if interval == monitor.watcher.get_interval():
                    mons.append(monitor)
        else:
            mons = self.account_watchers[account]
        return mons

    def slurp_unique_watchers(self, monitors, account, interval):
        unique_watcher_results = {}
        for monitor in monitors:
            app.logger.info("Running {} for {} ({} minutes interval)".format(monitor.watcher.i_am_singular, account, interval))
            (items, exception_map) = monitor.watcher.slurp()
            unique_watcher_results[monitor.watcher.index] = [items, exception_map]

        return unique_watcher_results

    def get_alerters(self, account):
        """ Return a list of alerters enabled for a specific account """
        return self.account_alerters[account]

    def get_intervals(self, account):
        """ Returns current intervals for watchers """
        buckets = []
        for monitor in self.get_watchauditors(account):
            interval = monitor.watcher.get_interval()
            if not interval in buckets:
                buckets.append(interval)
        return buckets

    def get_items_to_audit(self, monitor, auditor, slurped_watcher_results, monitors_with_changes):
        """
        Returns the items that have changed if there are no changes in dependencies,
        otherwise returns all slurped items for reauditing
        """
        monitor.watcher.full_audit_list = None
        if auditor.support_watcher_indexes:
            for support_watcher_index in auditor.support_watcher_indexes:
                if support_watcher_index in monitors_with_changes:
                    app.logger.debug("Upstream watcher changed {}. reauditing {}".format(support_watcher_index, monitor.watcher.index))
                    monitor.watcher.full_audit_list = slurped_watcher_results[0]
        if auditor.support_auditor_indexes:
            for support_auditor_index in auditor.support_auditor_indexes:
                if support_auditor_index in monitors_with_changes:
                    app.logger.debug("Upstream auditor changed {}. reauditing {}".format(support_auditor_index, monitor.watcher.index))
                    monitor.watcher.full_audit_list = slurped_watcher_results[0]

        if monitor.watcher.full_audit_list:
            return monitor.watcher.full_audit_list

        return [item for item in monitor.watcher.created_items + monitor.watcher.changed_items]
