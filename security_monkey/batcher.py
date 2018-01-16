"""
.. module: security_monkey.scheduler
    :platform: Unix
    :synopsis: Logic for batched watchers and auditors

.. version:: $$VERSION$$
.. moduleauthor:: Mike Grima <mgrima@netflix.com>

"""
from sqlalchemy.exc import OperationalError, InvalidRequestError, StatementError

from security_monkey import app, jirasync, db
from security_monkey.datastore import store_exception


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
            if len(audit_items) > 0:
                au.items = audit_items
                au.audit_objects()
                au.save_issues()
                if send_report:
                    report = au.create_report()
                    au.email_report(report)

                if jirasync:
                    app.logger.info('Syncing {} issues on {} with Jira'.format(au.index, monitor.watcher.accounts[0]))
                    jirasync.sync_issues(monitor.watcher.accounts, au.index)
            else:
                app.logger.debug("No durable changes to audit.")
    except (OperationalError, InvalidRequestError, StatementError) as e:
        app.logger.exception("Database error processing accounts %s, cleaning up session.", monitor.watcher.accounts[0])
        db.session.remove()
        store_exception("scheduler-audit-changes", None, e)
