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

from flask.ext.script import Manager, Command, Option
from security_monkey import app, db
from security_monkey.common.route53 import Route53Service
from gunicorn.app.base import Application

from flask.ext.migrate import Migrate, MigrateCommand

from security_monkey.scheduler import run_change_reporter as sm_run_change_reporter
from security_monkey.scheduler import find_changes as sm_find_changes
from security_monkey.scheduler import audit_changes as sm_audit_changes
from security_monkey.backup import backup_config_to_json as sm_backup_config_to_json

manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


@manager.command
def drop_db():
    """ Drops the database. """
    db.drop_all()


@manager.option('-a', '--accounts', dest='accounts', type=unicode, default=u'all')
def run_change_reporter(accounts):
    """ Runs Reporter """
    sm_run_change_reporter(accounts)


@manager.option('-a', '--accounts', dest='accounts', type=unicode, default=u'all')
@manager.option('-m', '--monitors', dest='monitors', type=unicode, default=u'all')
def find_changes(accounts, monitors):
    """Runs watchers"""
    sm_find_changes(accounts, monitors)


@manager.option('-a', '--accounts', dest='accounts', type=unicode, default=u'all')
@manager.option('-m', '--monitors', dest='monitors', type=unicode, default=u'all')
@manager.option('-r', '--send_report', dest='send_report', type=bool, default=False)
def audit_changes(accounts, monitors, send_report):
    """ Runs auditors """
    sm_audit_changes(accounts, monitors, send_report)


@manager.option('-a', '--accounts', dest='accounts', type=unicode, default=u'all')
@manager.option('-m', '--monitors', dest='monitors', type=unicode, default=u'all')
@manager.option('-o', '--outputfolder', dest='outputfolder', type=unicode, default=u'backups')
def backup_config_to_json(accounts, monitors, outputfolder):
    """Saves the most current item revisions to a json file."""
    sm_backup_config_to_json(accounts, monitors, outputfolder)


@manager.command
def start_scheduler():
    """ starts the python scheduler to run the watchers and auditors"""
    from security_monkey import scheduler
    scheduler.setup_scheduler()
    scheduler.scheduler.start()


@manager.option('-u', '--number', dest='number', type=unicode, required=True)
@manager.option('-a', '--active', dest='active', type=bool, default=True)
@manager.option('-t', '--thirdparty', dest='third_party', type=bool, default=False)
@manager.option('-n', '--name', dest='name', type=unicode, required=True)
@manager.option('-s', '--s3name', dest='s3_name', type=unicode, default=u'')
@manager.option('-o', '--notes', dest='notes', type=unicode, default=u'')
@manager.option('-f', '--force', dest='force', help='Override existing accounts', action='store_true')
def add_account(number, third_party, name, s3_name, active, notes, force):
    from security_monkey.common.utils.utils import add_account
    res = add_account(number, third_party, name, s3_name, active, notes, force)
    if res:
        app.logger.info('Successfully added account {}'.format(name))
    else:
        app.logger.info('Account with id {} already exists'.format(number))


class APIServer(Command):
    def __init__(self, host='127.0.0.1', port=app.config.get('API_PORT'), workers=6):
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

        class FlaskApplication(Application):
            def init(self, parser, opts, args):
                return {
                    'bind': address,
                    'workers': workers
                }

            def load(self):
                return app

        FlaskApplication().run()


if __name__ == "__main__":
    manager.add_command("run_api_server", APIServer())
    manager.run()
