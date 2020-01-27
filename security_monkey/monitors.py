"""
.. module: security_monkey.monitors
    :platform: Unix
    :synopsis: Monitors are a grouping of a watcher and it's associated auditor

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.auditor import auditor_registry
from security_monkey.watcher import watcher_registry
from security_monkey.account_manager import account_registry, get_account_by_name
from security_monkey import app


class Monitor(object):
    """Collects a watcher with the associated auditors"""
    def __init__(self, watcher_class, account, debug=False):
        self.watcher = watcher_class(accounts=[account.name], debug=debug)
        self.auditors = []
        self.audit_tier = 0
        self.batch_support = self.watcher.batched_size > 0

        for auditor_class in auditor_registry[self.watcher.index]:
            au = auditor_class([account.name], debug=debug)
            if au.applies_to_account(account):
                self.auditors.append(au)


def get_monitors(account_name, monitor_names, debug=False):
    """
    Returns a list of monitors in the correct audit order which apply to one or
    more of the accounts.
    """
    requested_mons = []
    account = get_account_by_name(account_name)
    account_manager = account_registry.get(account.account_type.name)()

    for monitor_name in monitor_names:
        watcher_class = watcher_registry[monitor_name]
        if account_manager.is_compatible_with_account_type(watcher_class.account_type):
            monitor = Monitor(watcher_class, account, debug)
            if monitor.watcher.is_active():
                requested_mons.append(monitor)

    return requested_mons


def get_monitors_and_dependencies(account, monitor_names, debug=False):
    """
    Returns a list of monitors in the correct audit order which apply to one or
    more of the accounts plus any monitors with audit results dependent on the
    ones requested.
    """
    monitors = all_monitors(account, debug)
    monitor_names = _find_dependent_monitors(monitors, monitor_names)
    requested_mons = []
    for mon in monitors:
        if mon.watcher.index in monitor_names:
            requested_mons.append(mon)

    return requested_mons


def all_monitors(account_name, debug=False):
    """
    Returns a list of all monitors in the correct audit order which apply to one
    or more of the accounts.
    """
    monitor_dict = {}
    account = get_account_by_name(account_name)
    account_manager = account_registry.get(account.account_type.name)()

    for watcher_class in watcher_registry.values():
        if account_manager.is_compatible_with_account_type(watcher_class.account_type):
            monitor = Monitor(watcher_class, account, debug)
            if monitor.watcher.is_active():
                monitor_dict[monitor.watcher.index] = monitor

    for mon in list(monitor_dict.values()):
        if (mon.auditors):
            path = [mon.watcher.index]
            _set_dependency_hierarchies(monitor_dict, mon, path, mon.audit_tier + 1)

    monitors = sorted(list(monitor_dict.values()), key=lambda item: item.audit_tier, reverse=True)
    return monitors


def _set_dependency_hierarchies(monitor_dict, monitor, path, level):
    declared_support_indexes = set()

    for auditor in monitor.auditors:
        declared_support_indexes |= set(auditor.support_auditor_indexes)

    for support_index in declared_support_indexes:
        current_path = path + [ support_index ]
        if support_index in path:
            auditor_flow = ''
            for index in current_path:
                auditor_flow = auditor_flow + '->' + index
            raise Exception('Detected circular dependency in support auditor', auditor_flow)

        support_mon = monitor_dict.get(support_index)
        if support_mon == None:
            app.logger.warn("Monitor {0} depends on monitor {1}, but {1} is unavailable"
                                    .format(monitor.watcher.index, support_index))
        else:
            if support_mon.audit_tier < level:
                support_mon.audit_tier = level

            _set_dependency_hierarchies(monitor_dict, support_mon, current_path, level + 1)

def _find_dependent_monitors(monitors, monitor_names):
    """
    Used to find all the monitors that re dependent on those in the original
    monitor_names to the list.
    """
    last_iteration_count = 0
    while len(monitor_names) != last_iteration_count:
        # May need to loop through the list mutiple times in the case of
        # chaining dependencies
        last_iteration_count = len(monitor_names)
        for mon in monitors:
            for auditor in mon.auditors:
                for support_index in auditor.support_auditor_indexes:
                    if support_index in monitor_names and mon.watcher.index not in monitor_names:
                        monitor_names.append(mon.watcher.index)
                for support_index in auditor.support_watcher_indexes:
                    if support_index in monitor_names and mon.watcher.index not in monitor_names:
                        monitor_names.append(mon.watcher.index)

    return monitor_names
