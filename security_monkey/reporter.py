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

    def __init__(self, accounts=None, alert_accounts=None, debug=False):
        self.account_watchers = {}
        self.account_alerters = {}
        if not alert_accounts:
            alert_accounts = accounts
        for account in accounts:
            self.account_watchers[account] = []
            for monitor in all_monitors():
                watcher = monitor.watcher_class(accounts=[account], debug=debug)
                auditor = monitor.auditor_class(accounts=[account], debug=debug) if monitor.has_auditor() else None
                self.account_watchers[account].append((watcher, auditor))

            if account in alert_accounts:
                self.account_alerters[account] = Alerter(watchers_auditors=self.account_watchers[account], account=account)

    def run(self, account, interval=None):
        """Starts the process of watchers -> auditors -> alerters -> watchers.save()"""
        app.logger.info("Starting work on account {}.".format(account))
        time1 = time.time()
        for (watcher, auditor) in self.get_watchauditors(account, interval):
            app.logger.info("Running {} for {} ({} minutes interval)".format(watcher.i_am_singular, account, interval))
            (items, exception_map) = watcher.slurp()
            watcher.find_changes(current=items, exception_map=exception_map)
            items_to_audit = [item for item in watcher.created_items + watcher.changed_items]

            if len(items_to_audit) > 0 and auditor is not None:
                auditor.audit_these_objects(items_to_audit)

            if auditor is not None:
                auditor.save_issues()

            watcher.save()
            app.logger.info("Account {} is done with {}".format(account, watcher.i_am_singular))

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
            for (w, a) in self.account_watchers[account]:
                if w and interval == w.get_interval():
                    mons.append((w,a))
        else:
            mons = self.account_watchers[account]
        return mons

    def get_alerters(self, account):
        """ Return a list of alerters enabled for a specific account """
        return self.account_alerters[account]

    def get_intervals(self, account):
        """ Returns current intervals for watchers """
        buckets = []
        for (w, _) in self.get_watchauditors(account):
            if w:
                interval = w.get_interval()
                if not interval in buckets:
                    buckets.append(interval)
        return buckets
