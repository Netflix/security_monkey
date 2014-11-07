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
#!/usr/bin/env python

from flask.ext.script import Manager, Command
from security_monkey import app, db
from security_monkey.datastore import Datastore
from security_monkey.common.route53 import Route53Service
from gunicorn.app.base import Application

from flask.ext.migrate import Migrate, MigrateCommand

from security_monkey.scheduler import run_change_reporter as sm_run_change_reporter
from security_monkey.scheduler import find_changes as sm_find_changes
from security_monkey.scheduler import audit_changes as sm_audit_changes


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

@manager.command
def start_scheduler():
    """ starts the python scheduler to run the watchers and auditors"""
    from security_monkey import scheduler
    import security_monkey
    security_monkey.setup_scheduler()
    scheduler.start()


class APIServer(Command):
    def __init__(self, host='127.0.0.1', port=7102, workers=6):
        self.host = host
        self.port = port
        self.workers = workers

    def handle(self, app, *args, **kwargs):

        if app.config.get('USE_ROUTE53'):
            route53 = Route53Service()
            route53.register(app.config.get('FQDN'), exclusive=True)

        workers = self.workers

        class FlaskApplication(Application):
            def init(self, parser, opts, args):
                return {
                    'bind': '{}:{}'.format(
                        '127.0.0.1',
                        app.config.get('API_PORT')
                        ),
                    'workers': workers
                }

            def load(self):
                return app

        FlaskApplication().run()


if __name__ == "__main__":
    manager.add_command("run_api_server", APIServer())
    manager.run()
