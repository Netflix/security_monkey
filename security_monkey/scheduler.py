"""
.. module: security_monkey.scheduler
    :platform: Unix
    :synopsis: Runs watchers, auditors, or reports on demand or on a schedule

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

from apscheduler.threadpool import ThreadPool
from apscheduler.scheduler import Scheduler

from security_monkey.datastore import Account
from security_monkey.monitors import all_monitors, get_monitor
from security_monkey.reporter import Reporter

from security_monkey import db

import traceback
import time

def __prep_accounts__(accounts):
    if accounts == 'all':
        accounts = Account.query.filter(Account.third_party==False).filter(Account.active==True).all()
        accounts = [account.name for account in accounts]
        return accounts
    else:
        return accounts.split(',')

def __prep_monitor_names__(monitor_names):
    if monitor_names == 'all':
        return [monitor.index for monitor in all_monitors()]
    else:
        return monitor_names.split(',')

def run_change_reporter(accounts):
    """ Runs Reporter """
    accounts = __prep_accounts__(accounts)
    reporter = Reporter(accounts=accounts, alert_accounts=accounts, debug=True)
    for account in accounts:
        reporter.run(account)

def find_changes(accounts, monitor_names, debug=True):
    monitor_names = __prep_monitor_names__(monitor_names)
    for monitor_name in monitor_names:
        monitor = get_monitor(monitor_name)
        _find_changes(accounts, monitor, debug)

def audit_changes(accounts, monitor_names, send_report, debug=True):
    monitor_names = __prep_monitor_names__(monitor_names)
    for monitor_name in monitor_names:
        monitor = get_monitor(monitor_name)
        if monitor.has_auditor():
            _audit_changes(accounts, monitor, send_report, debug)

def _find_changes(accounts, monitor, debug=True):
    """ Runs a watcher and auditor on changed items """
    accounts = __prep_accounts__(accounts)
    cw = monitor.watcher_class(accounts=accounts, debug=True)
    (items, exception_map) = cw.slurp()
    cw.find_changes(current=items, exception_map=exception_map)

    # Audit these changed items
    if monitor.has_auditor():
        items_to_audit = []
        for item in cw.created_items + cw.changed_items:
            cluster = monitor.item_class(region=item.region, account=item.account, name=item.name, config=item.new_config)
            items_to_audit.append(cluster)

        au = monitor.auditor_class(accounts=accounts, debug=True)
        au.audit_these_objects(items_to_audit)
        au.save_issues()

    cw.save()
    db.session.close()

def _audit_changes(accounts, monitor, send_report, debug=True):
    """ Runs an auditors on all items """
    accounts = __prep_accounts__(accounts)
    au = monitor.auditor_class(accounts=accounts, debug=True)
    au.audit_all_objects()

    if send_report:
        report = au.create_report()
        au.email_report(report)

    au.save_issues()
    db.session.close()

def run_account(account):
    """
    This should be refactored into Reporter.
    Runs the watchers/auditors for each account.
    Does not run the alerter.
    Times the operations and logs those results.
    """
    app.logger.info("Starting work on account {}.".format(account))
    time1 = time.time()
    for monitor in all_monitors():
        find_changes(accounts, monitor)
        app.logger.info("Account {} is done with {}".format(account, monitor.index))
    time2 = time.time()
    app.logger.info('Run Account %s took %0.1f s' % (account, (time2-time1)))


pool = ThreadPool(core_threads=25, max_threads=30, keepalive=0)
scheduler = Scheduler(standalone=True, threadpool=pool, coalesce=True, misfire_grace_time=30)
interval = 15

def setup_scheduler():
    """Sets up the APScheduler"""
    log = logging.getLogger('apscheduler')
    log.setLevel(app.config.get('LOG_LEVEL'))
    log.addHandler(handler)

    try:
        accounts = Account.query.filter(Account.third_party==False).filter(Account.active==True).all()
        accounts = [account.name for account in accounts]
        for account in accounts:
            print "Scheduler adding account {}".format(account)
            scheduler.add_interval_job(run_change_reporter, minutes=interval, args=[account])
            for monitor in all_monitors():
                if monitor.has_auditor():
                    scheduler.add_cron_job(_audit_changes, hour=10, day_of_week="mon-fri", args=[account, monitor, True])

    except Exception as e:
        app.logger.warn("Scheduler Exception: {}".format(e))
        app.logger.warn(traceback.format_exc())
