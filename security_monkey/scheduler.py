"""
.. module: security_monkey.scheduler
    :platform: Unix
    :synopsis: Runs watchers, auditors, or reports on demand or on a schedule

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

from apscheduler.threadpool import ThreadPool
from apscheduler import events
from apscheduler.scheduler import Scheduler
from sqlalchemy.exc import OperationalError, InvalidRequestError, StatementError

from security_monkey.datastore import Account, clear_old_exceptions, store_exception
from security_monkey.monitors import get_monitors, get_monitors_and_dependencies, all_monitors
from security_monkey.reporter import Reporter

from security_monkey import app, db, jirasync, sentry

import traceback
import logging
from datetime import datetime, timedelta


def run_change_reporter(account_names, interval=None):
    """ Runs Reporter """
    try:
        for account in account_names:
            reporter = Reporter(account=account, debug=True)
            reporter.run(account, interval)
    except (OperationalError, InvalidRequestError, StatementError) as e:
        app.logger.exception("Database error processing accounts %s, cleaning up session.", account_names)
        db.session.remove()
        store_exception("scheduler-run-change-reporter", None, e)


def find_changes(accounts, monitor_names, debug=True):
    """
        Runs the watcher and stores the result, re-audits all types to account
        for downstream dependencies.
    """
    for account_name in accounts:
        monitors = get_monitors(account_name, monitor_names, debug)
        for mon in monitors:
            cw = mon.watcher
            if mon.batch_support:
                batch_logic(mon, cw, account_name, debug)
            else:
                # Just fetch normally...
                (items, exception_map) = cw.slurp()
                cw.find_changes(current=items, exception_map=exception_map)
                cw.save()

    # Batched monitors have already been monitored, and they will be skipped over.
    audit_changes(accounts, monitor_names, False, debug)
    db.session.close()


def batch_logic(monitor, current_watcher, account_name, debug):
    # Fetch the full list of items that we need to obtain:
    _, exception_map = current_watcher.slurp_list()
    if len(exception_map) > 0:
        # Get the location tuple to collect the region:
        location = exception_map.keys()[0]
        if len(location) > 2:
            region = location[2]
        else:
            region = "unknown"

        app.logger.error("Exceptions have caused nothing to be fetched for {technology}"
                         "/{account}/{region}..."
                         " CANNOT CONTINUE FOR THIS WATCHER!".format(technology=current_watcher.i_am_plural,
                                                                     account=account_name,
                                                                     region=region))
        return

    while not current_watcher.done_slurping:
        app.logger.debug("Fetching a batch of {batch} items for {technology}/{account}.".format(
            batch=current_watcher.batched_size, technology=current_watcher.i_am_plural, account=account_name
        ))
        (items, exception_map) = current_watcher.slurp()

        audit_items = current_watcher.find_changes(current=items, exception_map=exception_map)
        _audit_specific_changes(monitor, audit_items, False, debug)

    # Delete the items that no longer exist:
    app.logger.debug("Deleting all items for {technology}/{account} that no longer exist.".format(
        technology=current_watcher.i_am_plural, account=account_name
    ))
    current_watcher.find_deleted_batch(account_name)


def audit_changes(accounts, monitor_names, send_report, debug=True, skip_batch=True):
    for account in accounts:
        monitors = get_monitors_and_dependencies(account, monitor_names, debug)
        for monitor in monitors:
            # Skip batch support monitors... They have already been monitored.
            if monitor.batch_support and skip_batch:
                continue

            _audit_changes(account, monitor.auditors, send_report, debug)


def disable_accounts(account_names):
    for account_name in account_names:
        account = Account.query.filter(Account.name == account_name).first()
        if account:
            app.logger.debug("Disabling account %s", account.name)
            account.active = False
            db.session.add(account)

    db.session.commit()
    db.session.close()


def enable_accounts(account_names):
    for account_name in account_names:
        account = Account.query.filter(Account.name == account_name).first()
        if account:
            app.logger.debug("Enabling account %s", account.name)
            account.active = True
            db.session.add(account)

    db.session.commit()
    db.session.close()


def _audit_changes(account, auditors, send_report, debug=True):
    """ Runs auditors on all items """
    try:
        for au in auditors:
            au.items = au.read_previous_items()
            au.audit_objects()
            # au.audit_all_objects()
            au.save_issues()
            if send_report:
                report = au.create_report()
                au.email_report(report)

            if jirasync:
                app.logger.info('Syncing {} issues on {} with Jira'.format(au.index, account))
                jirasync.sync_issues([account], au.index)
    except (OperationalError, InvalidRequestError, StatementError) as e:
        app.logger.exception("Database error processing accounts %s, cleaning up session.", account)
        db.session.remove()
        store_exception("scheduler-audit-changes", None, e)


def _audit_specific_changes(monitor, audit_items, send_report, debug=True):
    """
    Runs the auditor on specific items that are passed in.
    :param monitor:
    :param audit_items:
    :param send_report:
    :param debug:
    :return:
    """
    try:
        for au in monitor.auditors:
            au.items = audit_items
            au.audit_objects()
            au.save_issues()
            if send_report:
                report = au.create_report()
                au.email_report(report)

            if jirasync:
                app.logger.info('Syncing {} issues on {} with Jira'.format(au.index, monitor.watcher.accounts[0]))
                jirasync.sync_issues(monitor.watcher.accounts, au.index)
    except (OperationalError, InvalidRequestError, StatementError) as e:
        app.logger.exception("Database error processing accounts %s, cleaning up session.", monitor.watcher.accounts[0])
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
    misfire_grace_time=app.config.get('MISFIRE_GRACE_TIME', 30)
)


def exception_listener(event):
     store_exception("scheduler-change-reporter-uncaught", None, event.exception)

scheduler.add_listener(exception_listener, events.EVENT_JOB_ERROR)


def setup_scheduler():
    """Sets up the APScheduler"""
    log = logging.getLogger('apscheduler')

    try:
        accounts = Account.query.filter(Account.third_party == False).filter(Account.active == True).all()  # noqa
        accounts = [account.name for account in accounts]
        for account in accounts:
            app.logger.debug("Scheduler adding account {}".format(account))
            rep = Reporter(account=account)
            delay = app.config.get('REPORTER_START_DELAY', 10)

            for period in rep.get_intervals(account):
                scheduler.add_interval_job(
                    run_change_reporter,
                    minutes=period,
                    start_date=datetime.now()+timedelta(seconds=delay),
                    args=[[account], period]
                )
            auditors = []
            for monitor in all_monitors(account):
                auditors.extend(monitor.auditors)
            scheduler.add_cron_job(_audit_changes, hour=10, day_of_week="mon-fri", args=[account, auditors, True])

        # Clear out old exceptions:
        scheduler.add_cron_job(_clear_old_exceptions, hour=3, minute=0)

    except Exception as e:
        if sentry:
            sentry.captureException()
        app.logger.warn("Scheduler Exception: {}".format(e))
        app.logger.warn(traceback.format_exc())
        store_exception("scheduler", None, e)
