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
from datetime import datetime
import sys

from flask.ext.script import Manager, Command, Option, prompt_pass

from security_monkey.common.s3_canonical import get_canonical_ids, fetch_id
from security_monkey.datastore import clear_old_exceptions, store_exception, AccountType

from security_monkey import app, db
from security_monkey.common.route53 import Route53Service

from flask.ext.migrate import Migrate, MigrateCommand

from security_monkey.scheduler import run_change_reporter as sm_run_change_reporter
from security_monkey.scheduler import find_changes as sm_find_changes
from security_monkey.scheduler import audit_changes as sm_audit_changes
from security_monkey.scheduler import disable_accounts as sm_disable_accounts
from security_monkey.scheduler import enable_accounts as sm_enable_accounts
from security_monkey.backup import backup_config_to_json as sm_backup_config_to_json
from security_monkey.common.utils import find_modules, load_plugins
from security_monkey.datastore import Account
from security_monkey.watcher import watcher_registry

from swag_client.backend import SWAGManager
from swag_client.util import parse_swag_config_options

try:
    from gunicorn.app.base import Application

    GUNICORN = True
except ImportError:
    # Gunicorn does not yet support Windows.
    # See issue #524. https://github.com/benoitc/gunicorn/issues/524
    # For dev on Windows, make this an optional import.
    print('Could not import gunicorn, skipping.')
    GUNICORN = False

manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

find_modules('alerters')
find_modules('watchers')
find_modules('auditors')
load_plugins('security_monkey.plugins')


@manager.command
def drop_db():
    """ Drops the database. """
    db.drop_all()


@manager.option('-a', '--accounts', dest='accounts', type=unicode, default=u'all')
def run_change_reporter(accounts):
    """ Runs Reporter """
    account_names = _parse_accounts(accounts)
    sm_run_change_reporter(account_names)


@manager.option('-a', '--accounts', dest='accounts', type=unicode, default=u'all')
@manager.option('-m', '--monitors', dest='monitors', type=unicode, default=u'all')
def find_changes(accounts, monitors):
    """ Runs watchers """
    monitor_names = _parse_tech_names(monitors)
    account_names = _parse_accounts(accounts)
    sm_find_changes(account_names, monitor_names)


@manager.option('-a', '--accounts', dest='accounts', type=unicode, default=u'all')
@manager.option('-m', '--monitors', dest='monitors', type=unicode, default=u'all')
@manager.option('-r', '--send_report', dest='send_report', type=bool, default=False)
@manager.option('-s', '--skip_batch', dest='skip_batch', type=bool, default=True)
def audit_changes(accounts, monitors, send_report, skip_batch):
    """ Runs auditors """
    monitor_names = _parse_tech_names(monitors)
    account_names = _parse_accounts(accounts)
    sm_audit_changes(account_names, monitor_names, send_report, skip_batch=skip_batch)


@manager.option('-a', '--accounts', dest='accounts', type=unicode, default=u'all')
@manager.option('-m', '--monitors', dest='monitors', type=unicode, default=u'all')
def delete_unjustified_issues(accounts, monitors):
    """ Allows us to delete unjustified issues. """
    monitor_names = _parse_tech_names(monitors)
    account_names = _parse_accounts(accounts)
    from security_monkey.datastore import ItemAudit
    issues = ItemAudit.query.filter_by(justified=False).all()
    for issue in issues:
        del issue.sub_items[:]
        db.session.delete(issue)
    db.session.commit()


@manager.option('-a', '--accounts', dest='accounts', type=unicode, default=u'all')
@manager.option('-m', '--monitors', dest='monitors', type=unicode, default=u'all')
@manager.option('-o', '--outputfolder', dest='outputfolder', type=unicode, default=u'backups')
def backup_config_to_json(accounts, monitors, outputfolder):
    """ Saves the most current item revisions to a json file. """
    monitor_names = _parse_tech_names(monitors)
    account_names = _parse_accounts(accounts)
    sm_backup_config_to_json(account_names, monitor_names, outputfolder)


@manager.command
def start_scheduler():
    """ Starts the python scheduler to run the watchers and auditors """
    from security_monkey import scheduler
    scheduler.setup_scheduler()
    scheduler.scheduler.start()


@manager.command
def sync_jira():
    """ Syncs issues with Jira """
    from security_monkey import jirasync
    if jirasync:
        app.logger.info('Syncing issues with Jira')
        jirasync.sync_issues()
    else:
        app.logger.info('Jira sync not configured. Is SECURITY_MONKEY_JIRA_SYNC set?')


@manager.command
def clear_expired_exceptions():
    """
    Clears out the exception logs table of all exception entries that have expired past the TTL.
    :return:
    """
    print("Clearing out exceptions that have an expired TTL...")
    clear_old_exceptions()
    print("Completed clearing out exceptions that have an expired TTL.")


@manager.command
def amazon_accounts():
    """ Pre-populates standard AWS owned accounts """
    import json
    from security_monkey.datastore import Account, AccountType
    from os.path import dirname, join

    data_file = join(dirname(dirname(__file__)), "data", "aws_accounts.json")
    data = json.load(open(data_file, 'r'))

    app.logger.info('Adding / updating Amazon owned accounts')
    try:
        account_type_result = AccountType.query.filter(AccountType.name == 'AWS').first()
        if not account_type_result:
            account_type_result = AccountType(name='AWS')
            db.session.add(account_type_result)
            db.session.commit()
            db.session.refresh(account_type_result)

        for group, info in data.items():
            for aws_account in info['accounts']:
                acct_name = "{group} ({region})".format(group=group, region=aws_account['region'])
                account = Account.query.filter(Account.identifier == aws_account['account_id']).first()
                if not account:
                    app.logger.debug('    Adding account {0}'.format(acct_name))
                    account = Account()
                else:
                    app.logger.debug('    Updating account {0}'.format(acct_name))

                account.identifier = aws_account['account_id']
                account.account_type_id = account_type_result.id
                account.active = False
                account.third_party = True
                account.name = acct_name
                account.notes = info['url']

                db.session.add(account)

        db.session.commit()
        app.logger.info('Finished adding Amazon owned accounts')
    except Exception as e:
        app.logger.exception("An error occured while adding accounts")
        store_exception("manager-amazon-accounts", None, e)


@manager.command
@manager.option('-e', '--email', dest='email', type=unicode, required=True)
@manager.option('-r', '--role', dest='role', type=str, required=True)
def create_user(email, role):
    from flask_security import SQLAlchemyUserDatastore
    from security_monkey.datastore import User
    from security_monkey.datastore import Role
    from flask_security.utils import encrypt_password

    user_datastore = SQLAlchemyUserDatastore(db, User, Role)

    ROLES = ['View', 'Comment', 'Justify', 'Admin']
    if role not in ROLES:
        sys.stderr.write('[!] Role must be one of [{0}].\n'.format(' '.join(ROLES)))
        sys.exit(1)

    users = User.query.filter(User.email == email)

    if users.count() == 0:
        password1 = prompt_pass("Password")
        password2 = prompt_pass("Confirm Password")

        if password1 != password2:
            sys.stderr.write("[!] Passwords do not match\n")
            sys.exit(1)

        user = user_datastore.create_user(email=email,
                                          password=encrypt_password(password1),
                                          confirmed_at=datetime.now())
    else:
        sys.stdout.write("[+] Updating existing user\n")
        user = users.first()

    user.role = role

    db.session.add(user)
    db.session.commit()


@manager.option('-a', '--accounts', dest='accounts', type=unicode, default=u'all')
def disable_accounts(accounts):
    """ Bulk disables one or more accounts """
    account_names = _parse_accounts(accounts)
    sm_disable_accounts(account_names)


@manager.option('-a', '--accounts', dest='accounts', type=unicode, default=u'all')
def enable_accounts(accounts):
    """ Bulk enables one or more accounts """
    account_names = _parse_accounts(accounts, active=False)
    sm_enable_accounts(account_names)


@manager.option('-t', '--tech_name', dest='tech_name', type=str, required=True)
@manager.option('-m', '--method', dest='method', type=str, required=True)
@manager.option('-a', '--auditor', dest='auditor', type=str, required=True)
@manager.option('-s', '--score', dest='score', type=int, required=False)
@manager.option('-b', '--disabled', dest='disabled', type=bool, default=False)
@manager.option('-p', '--pattern_scores', dest='pattern_scores', type=str, required=False)
def add_override_score(tech_name, method, auditor, score, disabled, pattern_scores):
    """
    Adds an audit disable/override scores
    :param tech_name: technology index
    :param method: the neme of the auditor method to override
    :param auditor: The class name of the auditor containing the check method
    :param score: The default override score to assign to the check method issue
    :param disabled: Flag indicating whether the check method should be run
    :param pattern_scores: A comma separated list of account field values and scores.
           This can be used to override the default score based on some field in the account
           that the check method is running against. The format of each value/score is:
           account_type.account_field.account_value=score
    """
    from security_monkey.datastore import ItemAuditScore
    from security_monkey.auditor import auditor_registry

    if tech_name not in auditor_registry:
        sys.stderr.write('Invalid tech name {}.\n'.format(tech_name))
        sys.exit(1)

    valid = False
    auditor_classes = auditor_registry[tech_name]
    for auditor_class in auditor_classes:
        if auditor_class.__name__ == auditor:
            valid = True
            break
    if not valid:
        sys.stderr.write('Invalid auditor {}.\n'.format(auditor))
        sys.exit(1)

    if not getattr(auditor_class, method, None):
        sys.stderr.write('Invalid method {}.\n'.format(method))
        sys.exit(1)

    if score is None and not disabled:
        sys.stderr.write('Either score (-s) or disabled (-b) required')
        sys.exit(1)

    if score is None:
        score = 0

    query = ItemAuditScore.query.filter(ItemAuditScore.technology == tech_name)
    method_str = "{method} ({auditor})".format(method=method, auditor=auditor)
    query = query.filter(ItemAuditScore.method == method_str)
    entry = query.first()

    if not entry:
        entry = ItemAuditScore()
        entry.technology = tech_name
        entry.method = method_str

    entry.score = score
    entry.disabled = disabled

    if pattern_scores is not None:
        scores = pattern_scores.split(',')
        for score in scores:
            left_right = score.split('=')
            if len(left_right) != 2:
                sys.stderr.write('pattern_scores (-p) format account_type.account_field.account_value=score\n')
                sys.exit(1)

            account_info = left_right[0].split('.')
            if len(account_info) != 3:
                sys.stderr.write('pattern_scores (-p) format account_type.account_field.account_value=score\n')
                sys.exit(1)

            from security_monkey.account_manager import account_registry
            if account_info[0] not in account_registry:
                sys.stderr.write('Invalid account type {}\n'.format(account_info[0]))
                sys.exit(1)

            entry.add_or_update_pattern_score(account_info[0], account_info[1], account_info[2], int(left_right[1]))

    db.session.add(entry)
    db.session.commit()
    db.session.close()


@manager.option('-f', '--file_name', dest='file_name', type=str, required=True)
@manager.option('-m', '--mappings', dest='field_mappings', type=str, required=False)
def add_override_scores(file_name, field_mappings):
    """
    Refreshes the audit disable/override scores from a csv file. Old scores not in
     the csv will be removed.
    :param file_name: path to the csv file
    :param field_mappings: Comma separated list of mappings of known types to csv file
     headers. Ex. 'tech=Tech Name,score=default score'
    """
    from security_monkey.datastore import ItemAuditScore, AccountPatternAuditScore
    from security_monkey.auditor import auditor_registry
    import csv

    csvfile = open(file_name, 'r')
    reader = csv.DictReader(csvfile)
    errors = []

    mappings = {
        'tech': 'tech',
        'auditor': 'auditor',
        'method': 'method',
        'disabled': 'disabled',
        'score': 'score',
        'patterns': {}
    }

    if field_mappings:
        mapping_defs = field_mappings.split(',')
        for mapping_def in mapping_defs:
            mapping = mapping_def.split('=')
            if mapping[0] in mappings:
                mappings[mapping[0]] = mapping[1]
            else:
                patterns = mappings['patterns']
                patterns[mapping[0]] = mapping[1]

    line_num = 0
    entries = []
    for row in reader:
        line_num = line_num + 1
        tech_name = row[mappings['tech']]
        auditor = row[mappings['auditor']]
        method = row[mappings['method']]

        if not tech_name or not auditor or not method:
            continue

        score = None
        str_score = row[mappings['score']].decode('ascii', 'ignore').strip('')
        if str_score != '':
            if not str_score.isdigit():
                errors.append('Score {} line {} is not a positive int.'.format(str_score, line_num))
                continue
            score = int(str_score)

        if row[mappings['disabled']].lower() == 'true':
            disabled = True
        else:
            disabled = False

        if score is None and not disabled:
            continue

        if score is None:
            score = 0

        if tech_name not in auditor_registry:
            errors.append('Invalid tech name {} line {}.'.format(tech_name, line_num))
            continue

        valid = False
        auditor_classes = auditor_registry[tech_name]
        for auditor_class in auditor_classes:
            if auditor_class.__name__ == auditor:
                valid = True
                break

        if not valid:
            errors.append('Invalid auditor {} line {}.'.format(auditor, line_num))
            continue

        if not getattr(auditor_class, method, None):
            errors.append('Invalid method {} line {}.'.format(method, line_num))
            continue

        entry = ItemAuditScore(technology=tech_name, method=method + ' (' + auditor + ')',
                               score=score, disabled=disabled)

        pattern_mappings = mappings['patterns']
        for mapping in pattern_mappings:
            str_pattern_score = row[pattern_mappings[mapping]].decode('ascii', 'ignore').strip()
            if str_pattern_score != '':
                if not str_pattern_score.isdigit():
                    errors.append('Pattern score {} line {} is not a positive int.'.format(str_pattern_score, line_num))
                    continue

                account_info = mapping.split('.')
                if len(account_info) != 3:
                    errors.append('Invalid pattern mapping {}.'.format(mapping))
                    continue

                from security_monkey.account_manager import account_registry
                if account_info[0] not in account_registry:
                    errors.append('Invalid account type {}'.format(account_info[0]))
                    continue

                db_pattern_score = AccountPatternAuditScore(account_type=account_info[0],
                                                            account_field=account_info[1],
                                                            account_pattern=account_info[2],
                                                            score=int(str_pattern_score))

                entry.account_pattern_scores.append(db_pattern_score)

        entries.append(entry)

    if len(errors) > 0:
        for error in errors:
            sys.stderr.write("{}\n".format(error))
        sys.exit(1)

    AccountPatternAuditScore.query.delete()
    ItemAuditScore.query.delete()

    for entry in entries:
        db.session.add(entry)

    db.session.commit()
    db.session.close()


def _parse_tech_names(tech_str):
    if tech_str == 'all':
        return watcher_registry.keys()
    else:
        return tech_str.split(',')


def _parse_accounts(account_str, active=True):
    if account_str == 'all':
        accounts = Account.query.filter(Account.third_party == False).filter(Account.active == active).all()
        accounts = [account.name for account in accounts]
        return accounts
    else:
        names_or_ids = account_str.split(',')
        accounts = Account.query.all()
        accounts = {account.identifier: account.name for account in accounts}
        names = map(lambda n: accounts.get(n, n), names_or_ids)
        return names


@manager.option('-n', '--name', dest='name', type=unicode, required=True)
def delete_account(name):
    from security_monkey.account_manager import delete_account_by_name
    delete_account_by_name(name)


@manager.option('-t', '--tech_name', dest='tech_name', type=str, required=True)
@manager.option('-d', '--disabled', dest='disabled', type=bool, default=False)
# We are locking down the allowed intervals here to 15 minutes, 1 hour, 12 hours, 24
# hours or one week because too many different intervals could result in too many
# scheduler threads, impacting performance.
@manager.option('-i', '--interval', dest='interval', type=int, default=60, choices=[15, 60, 720, 1440, 10080])
def add_watcher_config(tech_name, disabled, interval):
    from security_monkey.datastore import WatcherConfig
    from security_monkey.watcher import watcher_registry

    if tech_name not in watcher_registry:
        sys.stderr.write('Invalid tech name {}.\n'.format(tech_name))
        sys.exit(1)

    query = WatcherConfig.query.filter(WatcherConfig.index == tech_name)
    entry = query.first()

    if not entry:
        entry = WatcherConfig()

    entry.index = tech_name
    entry.interval = interval
    entry.active = not disabled

    db.session.add(entry)
    db.session.commit()
    db.session.close()


@manager.option("--override", dest="override", type=bool, default=True)
def fetch_aws_canonical_ids(override):
    """
    Adds S3 canonical IDs in for all AWS accounts in SM.
    """
    app.logger.info("[ ] Fetching S3 canonical IDs for all AWS accounts being monitored by Security Monkey.")

    # Get all the active AWS accounts:
    accounts = Account.query.filter(Account.active == True) \
        .join(AccountType).filter(AccountType.name == "AWS").all()  # noqa

    get_canonical_ids(accounts, override=override)

    app.logger.info("[@] Completed canonical ID fetching.")


@manager.command
def clean_stale_issues():
    """
    Cleans up issues for auditors that have been removed
    """
    from security_monkey.common.audit_issue_cleanup import clean_stale_issues
    clean_stale_issues()


class APIServer(Command):
    def __init__(self, host='127.0.0.1', port=app.config.get('API_PORT'), workers=12):
        self.address = "{}:{}".format(host, port)
        self.workers = workers

    def get_options(self):
        return (
            Option('-b', '--bind',
                   dest='address',
                   type=str,
                   default=self.address),
            Option('-w', '--workers',
                   dest='workers',
                   type=int,
                   default=self.workers),
        )

    def handle(self, app, *args, **kwargs):

        if app.config.get('USE_ROUTE53'):
            route53 = Route53Service()
            route53.register(app.config.get('FQDN'), exclusive=True)

        workers = kwargs['workers']
        address = kwargs['address']

        if not GUNICORN:
            print('GUNICORN not installed. Try `runserver` to use the Flask debug server instead.')
        else:
            class FlaskApplication(Application):
                def init(self, parser, opts, args):
                    return {
                        'bind': address,
                        'workers': workers,
                        'timeout': 1800
                    }

                def load(self):
                    return app

            FlaskApplication().run()


@manager.option('-o', '--owner', type=unicode, required=True, help="Owner of the accounts, this is often set to a company name.")
@manager.option('-b', '--bucket-name', dest='bucket_name', type=unicode, required=True, help="S3 bucket where SWAG data is stored.")
@manager.option('-p', '--bucket-prefix', dest='bucket_prefix', type=unicode, default='accounts.json', help="Prefix to fetch account data from. Default: accounts.json")
@manager.option('-r', '--bucket-region', dest='bucket_region', type=unicode, default='us-east-1', help="Region SWAG S3 bucket is located. Default: us-east-1")
@manager.option('-t', '--account-type', dest='account_type', default='AWS', help="Type of account to sync from SWAG data. Default: AWS")
def sync_swag(owner, bucket_name, bucket_prefix, bucket_region, account_type):
    """Use the SWAG client to sync SWAG accounts to Security Monkey."""
    from security_monkey.account_manager import account_registry

    swag_opts = {
        'swag.type': 's3',
        'swag.bucket_name': bucket_name,
        'swag.data_file': bucket_prefix,
        'swag.region': bucket_region
    }

    swag = SWAGManager(**parse_swag_config_options(swag_opts))
    account_manager = account_registry[account_type]()

    for account in swag.get_all("[?provider=='{provider}']".format(provider=account_type.lower())):
        active = False
        for s in account['services']:
            if s['name'] == 'security_monkey':
                for status in s['status']:
                    if status['region'] == 'all':
                        active = status['enabled']

        thirdparty = True
        if account['owner'] == owner:
            thirdparty = False

        name = account['name']
        notes = account['description']
        identifier = account['id']

        account_manager.sync(account_manager.account_type, name, active, thirdparty,
                             notes, identifier,
                             custom_fields={})
    db.session.close()
    app.logger.info('SWAG sync successful.')


class AddAccount(Command):
    def __init__(self, account_manager, *args, **kwargs):
        super(AddAccount, self).__init__(*args, **kwargs)
        self._account_manager = account_manager
        self.__doc__ = "Add %s account" % account_manager.account_type

    def get_options(self):
        options = [
            Option('-n', '--name', type=unicode, required=True),
            Option('--id', dest='identifier', type=unicode, required=True),
            Option('--thirdparty', action='store_true'),
            Option('--active', action='store_true'),
            Option('--notes', type=unicode),
            Option('--update-existing', action="store_true")
        ]
        for cf in self._account_manager.custom_field_configs:
            options.append(Option('--%s' % cf.name, dest=cf.name, type=str))
        return options

    def handle(self, app, *args, **kwargs):
        name = kwargs.pop('name')
        active = kwargs.pop('active', False)
        thirdparty = kwargs.pop('thirdparty', False)
        notes = kwargs.pop('notes', u'')
        identifier = kwargs.pop('identifier')
        update = kwargs.pop('update_existing', False)
        if update:
            result = self._account_manager.update(None, self._account_manager.account_type, name, active, thirdparty,
                                                  notes, identifier,
                                                  custom_fields=kwargs
                                                  )
        else:
            result = self._account_manager.create(
                self._account_manager.account_type,
                name, active, thirdparty, notes, identifier,
                custom_fields=kwargs)
        db.session.close()

        if not result:
            return -1


def main():
    from security_monkey.account_manager import account_registry

    for name, account_manager in account_registry.items():
        manager.add_command("add_account_%s" % name.lower(), AddAccount(account_manager()))
    manager.add_command("run_api_server", APIServer())
    manager.run()


if __name__ == "__main__":
    main()
