"""
.. module: security_monkey.scheduler
    :platform: Unix
    :synopsis: Runs watchers, auditors, or reports on demand or on a schedule

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

from apscheduler.threadpool import ThreadPool
from apscheduler.scheduler import Scheduler
from sqlalchemy.exc import OperationalError, InvalidRequestError, StatementError

from security_monkey.datastore import Account, clear_old_exceptions, store_exception
from security_monkey.monitors import get_monitors
from security_monkey.reporter import Reporter

from security_monkey import app, db, jirasync

import traceback
import logging
from datetime import datetime, timedelta


def run_change_reporter(account_names, interval=None):
    """ Runs Reporter """
    try:
        for account in account_names:
            reporter = Reporter(account=account, alert_accounts=account_names, debug=True)
            reporter.run(account, interval)
    except (OperationalError, InvalidRequestError, StatementError) as e:
        app.logger.exception("Database error processing accounts %s, cleaning up session.", account_names)
        db.session.remove()
        store_exception("scheduler-run-change-reporter", None, e)


def find_changes(accounts, monitor_names, debug=True):
    monitors = get_monitors(accounts, monitor_names, debug)
    for monitor in monitors:
        cw = monitor.watcher
        (items, exception_map) = cw.slurp()
        cw.find_changes(current=items, exception_map=exception_map)
        cw.save()

    audit_changes(accounts, monitor_names, False, debug)
    db.session.close()


def audit_changes(accounts, monitor_names, send_report, debug=True):
    monitors = get_monitors(accounts, monitor_names, debug)
    for monitor in monitors:
        _audit_changes(monitor.auditors, send_report, debug)


def _audit_changes(auditors, send_report, debug=True):
    """ Runs auditors on all items """
    accounts = []
    try:
        for au in auditors:
            accounts = au.accounts
            au.audit_all_objects()
            au.save_issues()
            if send_report:
                report = au.create_report()
                au.email_report(report)

            if jirasync:
                app.logger.info('Syncing {} issues on {} with Jira'.format(au.index, accounts))
                jirasync.sync_issues(accounts, au.index)
    except (OperationalError, InvalidRequestError, StatementError) as e:
        app.logger.exception("Database error processing accounts %s, cleaning up session.", accounts)
        db.session.remove()
        store_exception("scheduler-audit-changes", None, e)


def _clear_old_exceptions():
    print("Clearing out exceptions that have an expired TTL...")
    clear_old_exceptions()
    print("Completed clearing out exceptions that have an expired TTL.")


pool = ThreadPool(
    core_threads=app.config.get('CORE_THREADS', 25),
    max_threads=app.config.get('MAX_THREADS', 30),
    keepalive=0
)
scheduler = Scheduler(
    standalone=True,
    threadpool=pool,
    coalesce=True,
    misfire_grace_time=30
)


def setup_scheduler():
    """Sets up the APScheduler"""
    log = logging.getLogger('apscheduler')

    try:
        accounts = Account.query.filter(Account.third_party == False).filter(Account.active == True).all()  # noqa
        accounts = [account.name for account in accounts]
        for account in accounts:
            print "Scheduler adding account {}".format(account)
            rep = Reporter(account=account)
            for period in rep.get_intervals(account):
                scheduler.add_interval_job(
                    run_change_reporter,
                    minutes=period,
                    start_date=datetime.now()+timedelta(seconds=2),
                    args=[[account], period]
                )
            auditors = []
            for monitor in rep.get_watchauditors(account):
                auditors.extend(monitor.auditors)
            scheduler.add_cron_job(_audit_changes, hour=10, day_of_week="mon-fri", args=[auditors, True])

        # Clear out old exceptions:
        scheduler.add_cron_job(_clear_old_exceptions, hour=3, minute=0)

    except Exception as e:
        app.logger.warn("Scheduler Exception: {}".format(e))
        app.logger.warn(traceback.format_exc())
        store_exception("scheduler", None, e)
