"""
.. module: security_monkey.monitors
    :platform: Unix
    :synopsis: Monitors are a grouping of a watcher and it's associated auditor

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey import app
from security_monkey.auditor import auditor_registry
from security_monkey.watcher import watcher_registry

class Monitor(object):
    """Collects a watcher with the associated auditors"""
    def __init__(self, watcher_class, accounts, debug=False):
        self.watcher = watcher_class(accounts=accounts, debug=debug)
        self.auditors = []
        for auditor_class in auditor_registry[self.watcher.index]:
            self.auditors.append(auditor_class(accounts=accounts, debug=debug))

def get_monitors(accounts, monitor_names, debug=False):
    """
    Returns a list of monitors in the correct audit order which apply to one or
    more of the accounts.
    """
    requested_mons = []
    for monitor_name in monitor_names:
        watcher_class = watcher_registry[monitor_name]
        monitor = Monitor(watcher_class, accounts, debug)
        requested_mons.append(monitor)

    return requested_mons

def all_monitors(accounts, debug=False):
    """
    Returns a list of all monitors in the correct audit order which apply to one
    or more of the accounts.
    """
    monitors = []

    for watcher_class in watcher_registry.itervalues():
        monitor = Monitor(watcher_class, accounts, debug)
        monitors.append(monitor)

    return monitors
