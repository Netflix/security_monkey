# encoding=utf8
"""
.. module: security_monkey.task_scheduler.tasks
    :platform: Unix
    :synopsis: Sets up the Celery task scheduling for watching, auditing, and reporting changes in the environment.

.. version:: $$VERSION$$
.. moduleauthor:: Mike Grima <mgrima@netflix.com>

"""
import sys
import importlib

try:
    importlib.reload(sys)  # Python 2
except NameError:
    pass  # Python 3

import time
import traceback

from security_monkey import app, db, jirasync, sentry
from security_monkey.alerter import Alerter
from security_monkey.datastore import store_exception, clear_old_exceptions, Technology, Account, Item, ItemRevision
from security_monkey.monitors import get_monitors, get_monitors_and_dependencies
from security_monkey.reporter import Reporter
from security_monkey.task_scheduler.util import CELERY, setup
import boto3
from sqlalchemy.exc import OperationalError, InvalidRequestError, StatementError


@CELERY.task(bind=True, max_retries=3)
def task_account_tech(self, account_name, technology_name):
    setup()
    app.logger.info("[ ] Executing Celery task for account: {}, technology: {}".format(account_name, technology_name))
    time1 = time.time()

    # Verify that the account exists (was it deleted? was it renamed?):
    if not Account.query.filter(Account.name == account_name).first():
        app.logger.error("[X] Account has been removed or renamed: {}. Please restart the scheduler to fix.".format(
            account_name
        ))
        return

    try:
        reporter_logic(account_name, technology_name)

        time2 = time.time()
        app.logger.info('[@] Run Account for Technology (%s/%s) took %0.1f s' % (account_name,
                                                                                 technology_name, (time2 - time1)))
        app.logger.info(
            "[+] Completed Celery task for account: {}, technology: {}".format(account_name, technology_name))
    except Exception as e:
        if sentry:
            sentry.captureException()
        app.logger.error("[X] Task Account Scheduler Exception ({}/{}): {}".format(account_name, technology_name, e))
        app.logger.error(traceback.format_exc())
        store_exception("scheduler-exception-on-watch", None, e)
        raise self.retry(exc=e)


@CELERY.task(bind=True, max_retries=3)
def task_audit(self, account_name, technology_name):
    setup()

    app.logger.info("[ ] Executing Celery task to audit changes for Account: {} Technology: {}".format(account_name,
                                                                                                       technology_name))
    # Verify that the account exists (was it deleted? was it renamed?):
    if not Account.query.filter(Account.name == account_name).first():
        app.logger.error("[X] Account has been removed or renamed: {}. Please restart the scheduler to fix.".format(
            account_name
        ))
        return

    try:
        audit_changes([account_name], [technology_name], True)

        app.logger.info("[+] Completed Celery task for account: {}, technology: {}".format(account_name,
                                                                                           technology_name))

    except Exception as e:
        if sentry:
            sentry.captureException()
        app.logger.error("[X] Task Audit Scheduler Exception ({}/{}): {}".format(account_name, technology_name, e))
        app.logger.error(traceback.format_exc())
        store_exception("scheduler-exception-on-audit", None, e)
        self.retry(exc=e)


@CELERY.task()
def clear_expired_exceptions():
    app.logger.info("[ ] Clearing out exceptions that have an expired TTL...")
    clear_old_exceptions()
    app.logger.info("[-] Completed clearing out exceptions that have an expired TTL.")


def fix_orphaned_deletions(account_name, technology_name):
    """
    Possible issue with orphaned items. This will check if there are any, and will assume that the item
    was deleted. This will create a deletion change record to it.

    :param account_name:
    :param technology_name:
    :return:
    """
    # If technology doesn't exist, then create it:
    technology = Technology.query.filter(Technology.name == technology_name).first()
    if not technology:
        technology = Technology(name=technology_name)
        db.session.add(technology)
        db.session.commit()
        app.logger.info("Technology: {} did not exist... created it...".format(technology_name))

    account = Account.query.filter(Account.name == account_name).one()

    # Query for orphaned items of the given technology/account pair:
    orphaned_items = Item.query.filter(Item.account_id == account.id, Item.tech_id == technology.id,
                                       Item.latest_revision_id == None).all()  # noqa

    if not orphaned_items:
        app.logger.info("[@] No orphaned items have been found. (This is good)")
        return

    # Fix the orphaned items:
    for oi in orphaned_items:
        app.logger.error("[?] Found an orphaned item: {}. Creating a deletion record for it".format(oi.name))
        revision = ItemRevision(active=False, config={})
        oi.revisions.append(revision)
        db.session.add(revision)
        db.session.add(oi)
        db.session.commit()

        # Update the latest revision id:
        db.session.refresh(revision)
        oi.latest_revision_id = revision.id
        db.session.add(oi)

        db.session.commit()
        app.logger.info("[-] Created deletion record for item: {}.".format(oi.name))


def reporter_logic(account_name, technology_name):
    """Logic for the run change reporter"""
    try:
        # Before doing anything... Look for orphaned items for this given technology. If they exist, then delete them:
        fix_orphaned_deletions(account_name, technology_name)

        # Watch and Audit:
        monitors = find_changes(account_name, technology_name)

        # Alert:
        app.logger.info("[ ] Sending alerts (if applicable) for account: {}, technology: {}".format(account_name,
                                                                                                    technology_name))
        Alerter(monitors, account=account_name).report()
    except (OperationalError, InvalidRequestError, StatementError) as e:
        app.logger.exception("[X] Database error processing account %s - technology %s cleaning up session.",
                             account_name, technology_name)
        db.session.remove()
        store_exception("scheduler-task-account-tech", None, e)
        raise e


def manual_run_change_reporter(accounts):
    """Manual change reporting from the command line"""
    app.logger.info("[ ] Executing manual change reporter task...")

    try:
        for account in accounts:
            time1 = time.time()
            rep = Reporter(account=account)

            for monitor in rep.all_monitors:
                if monitor.watcher:
                    app.logger.info("[ ] Running change finder for "
                                    "account: {} technology: {}".format(account, monitor.watcher.index))
                    reporter_logic(account, monitor.watcher.index)

            time2 = time.time()
            app.logger.info('[@] Run Account %s took %0.1f s' % (account, (time2 - time1)))

        app.logger.info("[+] Completed manual change reporting.")
    except (OperationalError, InvalidRequestError, StatementError) as e:
        app.logger.exception("[X] Database error processing cleaning up session.")
        db.session.remove()
        store_exception("scheduler-run-change-reporter", None, e)
        raise e


def manual_run_change_finder(accounts, technologies):
    """Manual change finder"""
    app.logger.info("[ ] Executing manual find changes task...")

    try:
        for account in accounts:
            time1 = time.time()

            for tech in technologies:
                find_changes(account, tech)

            time2 = time.time()
            app.logger.info('[@] Run Account %s took %0.1f s' % (account, (time2 - time1)))
        app.logger.info("[+] Completed manual change finder.")
    except (OperationalError, InvalidRequestError, StatementError) as e:
        app.logger.exception("[X] Database error processing cleaning up session.")
        db.session.remove()
        store_exception("scheduler-run-change-reporter", None, e)
        raise e


def find_changes(account_name, monitor_name, debug=True):
    """
        Runs the watcher and stores the result, re-audits all types to account
        for downstream dependencies.
    """
    # Before doing anything... Look for orphaned items for this given technology. If they exist, then delete them:
    fix_orphaned_deletions(account_name, monitor_name)

    monitors = get_monitors(account_name, [monitor_name], debug)

    items = []
    for mon in monitors:
        cw = mon.watcher
        app.logger.info("[-->] Looking for changes in account: {}, technology: {}".format(account_name, cw.index))
        if mon.batch_support:
            batch_logic(mon, cw, account_name, debug)
        else:
            # Just fetch normally...
            (items, exception_map) = cw.slurp() or ([], {})

            _post_metric(
                'queue_items_added',
                len(items),
                account_name=account_name,
                tech=cw.i_am_singular
            )

            cw.find_changes(current=items, exception_map=exception_map)

            cw.save()

    # Batched monitors have already been monitored, and they will be skipped over.
    audit_changes([account_name], [monitor_name], False, debug, items_count=len(items))
    db.session.close()

    return monitors


def audit_changes(accounts, monitor_names, send_report, debug=True, skip_batch=True, items_count=None):
    """
    Audits changes in the accounts
    :param accounts:
    :param monitor_names:
    :param send_report:
    :param debug:
    :param skip_batch:
    :return:
    """
    for account in accounts:
        monitors = get_monitors_and_dependencies(account, monitor_names, debug)
        for monitor in monitors:
            # Skip batch support monitors... They have already been monitored.
            if monitor.batch_support and skip_batch:
                continue

            app.logger.debug("[-->] Auditing account: {}, technology: {}".format(account, monitor.watcher.index))
            _audit_changes(account, monitor.auditors, send_report, debug)

            _post_metric(
                'queue_items_completed',
                items_count,
                account_name=account,
                tech=monitor.watcher.i_am_singular
            )


def batch_logic(monitor, current_watcher, account_name, debug):
    """
    Performs the batch watcher finding and auditing.

    TODO: Investigate how this could, in the future, be set to parallelize the batches.
    :param monitor:
    :param current_watcher:
    :param account_name:
    :param debug:
    :return:
    """
    # Fetch the full list of items that we need to obtain:
    _, exception_map = current_watcher.slurp_list()
    if len(exception_map) > 0:
        # Get the location tuple to collect the region:
        location = list(exception_map.keys())[0]
        if len(location) > 2:
            region = location[2]
        else:
            region = "unknown"

        exc_strings = [str(exc) for exc in list(exception_map.values())]

        app.logger.error("[X] Exceptions have caused nothing to be fetched for {technology}"
                         "/{account}/{region}..."
                         " CANNOT CONTINUE FOR THIS WATCHER!\n"
                         "Exceptions encountered were: {e}".format(technology=current_watcher.i_am_plural,
                                                                   account=account_name,
                                                                   region=region,
                                                                   e=",".join(exc_strings)))
        return

    while not current_watcher.done_slurping:
        app.logger.debug("[-->] Fetching a batch of {batch} items for {technology}/{account}.".format(
            batch=current_watcher.batched_size, technology=current_watcher.i_am_plural, account=account_name
        ))
        (items, exception_map) = current_watcher.slurp()

        _post_metric(
            'queue_items_added',
            len(items),
            account_name=account_name,
            tech=current_watcher.i_am_singular
        )

        audit_items = current_watcher.find_changes(current=items, exception_map=exception_map)
        _audit_specific_changes(monitor, audit_items, False, debug)

        _post_metric(
            'queue_items_completed',
            len(items),
            account_name=account_name,
            tech=current_watcher.i_am_singular
        )

    # Delete the items that no longer exist:
    app.logger.debug("[-->] Deleting all items for {technology}/{account} that no longer exist.".format(
        technology=current_watcher.i_am_plural, account=account_name
    ))
    current_watcher.find_deleted_batch(account_name)


def _audit_changes(account, auditors, send_report, debug=True):
    """ Runs auditors on all items """
    try:
        for au in auditors:
            au.items = au.read_previous_items()
            au.audit_objects()
            au.save_issues()
            if send_report:
                report = au.create_report()
                au.email_report(report)

            if jirasync:
                app.logger.info('[-->] Syncing {} issues on {} with Jira'.format(au.index, account))
                jirasync.sync_issues([account], au.index)
    except (OperationalError, InvalidRequestError, StatementError) as e:
        app.logger.exception("[X] Database error processing accounts %s, cleaning up session.", account)
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
                app.logger.info('[-->] Syncing {} issues on {} with Jira'.format(au.index, monitor.watcher.accounts[0]))
                jirasync.sync_issues(monitor.watcher.accounts, au.index)
    except (OperationalError, InvalidRequestError, StatementError) as e:
        app.logger.exception("[X] Database error processing accounts %s, cleaning up session.",
                             monitor.watcher.accounts[0])
        db.session.remove()
        store_exception("scheduler-audit-changes", None, e)


def _post_metric(event_type, amount, account_name=None, tech=None):
    if not app.config.get('METRICS_ENABLED', False):
        return

    cw_client = boto3.client('cloudwatch', region_name=app.config.get('METRICS_POST_REGION', 'us-east-1'))
    cw_client.put_metric_data(
        Namespace=app.config.get('METRICS_NAMESPACE', 'securitymonkey'),
        MetricData=[
            {
                'MetricName': event_type,
                'Timestamp': int(time.time()),
                'Value': amount,
                'Unit': 'Count',
                'Dimensions': [
                    {
                        'Name': 'tech',
                        'Value': tech
                    },
                    {
                        'Name': 'account_number',
                        'Value': Account.query.filter(Account.name == account_name).first().identifier
                    }
                ]
            }
        ]
    )
