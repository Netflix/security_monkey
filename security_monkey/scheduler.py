"""
.. module: security_monkey.scheduler
    :platform: Unix
    :synopsis: Runs watchers, auditors, or reports on demand or on a schedule

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

from apscheduler.threadpool import ThreadPool
from apscheduler.scheduler import Scheduler

from security_monkey.datastore import Account, Item, ItemRevision, Tag, Technology, Datastore
from security_monkey.monitors import all_monitors, get_monitor
from security_monkey.reporter import Reporter

from security_monkey import app, db, handler, jirasync

import traceback
import logging
from datetime import datetime, timedelta


def _prep_accounts(accounts):
    if accounts == 'all':
        accounts = Account.query.filter(Account.third_party==False).filter(Account.active==True).all()
        accounts = [account.name for account in accounts]
        return accounts
    else:
        return accounts.split(',')


def _prep_monitor_names(monitor_names):
    if monitor_names == 'all':
        return [monitor.index for monitor in all_monitors()]
    else:
        return monitor_names.split(',')


def run_change_reporter(accounts, interval=None):
    """ Runs Reporter """
    accounts = _prep_accounts(accounts)
    reporter = Reporter(accounts=accounts, alert_accounts=accounts, debug=True)
    for account in accounts:
        reporter.run(account, interval)


def find_changes(accounts, monitor_names, debug=True):
    monitor_names = _prep_monitor_names(monitor_names)
    for monitor_name in monitor_names:
        monitor = get_monitor(monitor_name)
        _find_changes(accounts, monitor, debug)


def save_tags(accounts, monitor_names, debug=True):
    accounts = _prep_accounts(accounts)
    monitor_names = _prep_monitor_names(monitor_names)
    query = Item.query.join((ItemRevision, Item.latest_revision_id == ItemRevision.id))
    query = query.join((Account, Account.id == Item.account_id))
    query = query.join((Technology, Technology.id == Item.tech_id))
    query = query.filter(Account.name.in_(accounts))
    query = query.filter(Technology.name.in_(monitor_names))

    items = query.all()
    app.logger.info("Checking Tags on {} items.".format(len(items)))
    count = 0
    for item in items:
        app.logger.info("Checking tags on item {} - {}".format(count, item.name))
        config = item.revisions[0].config
        Datastore.update_tags(item, config)
        db.session.add(item)
        count = count + 1
        if count % 100 == 0:
            app.logger.info("Finished 100/{} items. Commiting and continuing.".format(len(items)))
            db.session.commit()

    db.session.commit()


def audit_changes(accounts, monitor_names, send_report, debug=True):
    monitor_names = _prep_monitor_names(monitor_names)
    accounts = _prep_accounts(accounts)
    auditors = []
    for monitor_name in monitor_names:
        monitor = get_monitor(monitor_name)
        if monitor.has_auditor():
            auditors.append(monitor.auditor_class(accounts=accounts, debug=True))
    if auditors:
        _audit_changes(accounts, auditors, send_report, debug)


def _find_changes(accounts, monitor, debug=True):
    """ Runs a watcher and auditor on changed items """
    accounts = _prep_accounts(accounts)
    cw = monitor.watcher_class(accounts=accounts, debug=True)
    (items, exception_map) = cw.slurp()
    cw.find_changes(current=items, exception_map=exception_map)

    # Audit these changed items
    if monitor.has_auditor():
        items_to_audit = [item for item in cw.created_items + cw.changed_items]

        au = monitor.auditor_class(accounts=accounts, debug=True)
        au.audit_these_objects(items_to_audit)
        au.save_issues()

    cw.save()
    db.session.close()


def _audit_changes(accounts, auditors, send_report, debug=True):
    """ Runs auditors on all items """
    for au in auditors:
        au.audit_all_objects()
        au.save_issues()
        if send_report:
            report = au.create_report()
            au.email_report(report)

        if jirasync:
            app.logger.info('Syncing {} issues on {} with Jira'.format(au.index, accounts))
            jirasync.sync_issues(accounts, au.index)


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
    log.setLevel(app.config.get('LOG_LEVEL'))
    log.addHandler(handler)

    try:
        accounts = Account.query.filter(Account.third_party==False).filter(Account.active==True).all()
        accounts = [account.name for account in accounts]
        for account in accounts:
            print "Scheduler adding account {}".format(account)
            rep = Reporter(accounts=[account])
            for period in rep.get_intervals(account):
                scheduler.add_interval_job(
                    run_change_reporter,
                    minutes=period,
                    start_date=datetime.now()+timedelta(seconds=2),
                    args=[account, period]
                )
            auditors = [a for (_, a) in rep.get_watchauditors(account) if a]
            if auditors:
                scheduler.add_cron_job(_audit_changes, hour=10, day_of_week="mon-fri", args=[account, auditors, True])

    except Exception as e:
        app.logger.warn("Scheduler Exception: {}".format(e))
        app.logger.warn(traceback.format_exc())
