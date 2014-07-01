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

from security_monkey import run_change_reporter as sm_run_change_reporter
from security_monkey import find_rds_changes as sm_find_rds_changes
from security_monkey import find_elb_changes as sm_find_elb_changes
from security_monkey import find_iamssl_changes as sm_find_iamssl_changes
from security_monkey import find_sg_changes as sm_find_sg_changes
from security_monkey import find_s3_changes as sm_find_s3_changes
from security_monkey import find_iamuser_changes as sm_find_iamuser_changes
from security_monkey import find_iamgroup_changes as sm_find_iamgroup_changes
from security_monkey import find_iamrole_changes as sm_find_iamrole_changes
from security_monkey import find_keypair_changes as sm_find_keypair_changes
from security_monkey import find_sqs_changes as sm_find_sqs_changes
from security_monkey import find_sns_changes as sm_find_sns_changes

from security_monkey import audit_sns as sm_audit_sns
from security_monkey import audit_sg as sm_audit_sg
from security_monkey import audit_rds as sm_audit_rds
from security_monkey import audit_s3 as sm_audit_s3
from security_monkey import audit_iamuser as sm_audit_iamuser

manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


@manager.command
def create_db():
  """ Creates a database with all of the tables defined in
      your Alchemy models.
      DEPRECATED.  Use `python manage.py db upgrade`
  """
  #db.create_all()
  raise Exception("Received a call to create_db. Instead, please allow flask-migrate to create " +
                  "the database by calling `python manage.py db upgrade`.")


@manager.command
def drop_db():
  """ Drops the database.
  """
  db.drop_all()


@manager.command
def test_datastore():
  """ Tries to save garbage data to the DB """
  datastore = Datastore()
  mydict = {"fingerprint": "9d:bc:c5:f3:a6:12:9e:0b:b5:f3:3c:93:0e:32:78:80:9c:a9:ce:8c"}
  datastore.store("keypair", "us-east-1", "seg", "myname", True, mydict)
  for itemrevision in datastore.get("keypair", "us-east-1", "seg", "myname"):
    print itemrevision.__dict__


@manager.command
def run_change_reporter(accounts):
  """ Runs Reporter """
  sm_run_change_reporter(accounts)

#### CHANGE WATCHERS ####


@manager.command
def find_elb_changes(accounts):
  """ Runs watchers/elb"""
  sm_find_elb_changes(accounts)


@manager.command
def find_iamssl_changes(accounts):
  """ Runs watchers/iam_ssl"""
  sm_find_iamssl_changes(accounts)


@manager.command
def find_rds_changes(accounts):
  """ Runs watchers/rds_security_group"""
  sm_find_rds_changes(accounts)


@manager.command
def find_sg_changes(accounts):
  """ Runs watchers/security_group"""
  sm_find_sg_changes(accounts)


@manager.command
def find_s3_changes(accounts):
  """ Runs watchers/s3"""
  sm_find_s3_changes(accounts)


@manager.command
def find_iamuser_changes(accounts):
  """ Runs watchers/iamuser"""
  sm_find_iamuser_changes(accounts)


@manager.command
def find_iamgroup_changes(accounts):
  """ Runs watchers/iamgroup"""
  sm_find_iamgroup_changes(accounts)


@manager.command
def find_iamrole_changes(accounts):
  """ Runs watchers/iamrole"""
  sm_find_iamrole_changes(accounts)


@manager.command
def find_keypair_changes(accounts):
  """ Runs watchers/keypair"""
  sm_find_keypair_changes(accounts)


@manager.command
def find_sqs_changes(accounts):
  """ Runs watchers/sqs"""
  sm_find_sqs_changes(accounts)


@manager.command
def find_sns_changes(accounts):
  """ Runs watchers/sns """
  sm_find_sns_changes(accounts)


#### AUDITORS ####
@manager.option('-a', '--accounts', dest='accounts', type=unicode, default=u'all')
@manager.option('-r', '--send_report', dest='send_report', type=bool, default=False)
def audit_sns(accounts, send_report):
  """ Runs auditors/sns """
  sm_audit_sns(accounts, send_report)


@manager.option('-a', '--accounts', dest='accounts', type=unicode, default=u'all')
@manager.option('-r', '--send_report', dest='send_report', type=bool, default=False)
def audit_sg(accounts, send_report):
  """ Runs auditors/security_group """
  sm_audit_sg(accounts, send_report)


@manager.option('-a', '--accounts', dest='accounts', type=unicode, default=u'all')
@manager.option('-r', '--send_report', dest='send_report', type=bool, default=False)
def audit_rds(accounts, send_report):
  """ Runs auditors/rds_security_group """
  sm_audit_rds(accounts, send_report)


@manager.option('-a', '--accounts', dest='accounts', type=unicode, default=u'all')
@manager.option('-r', '--send_report', dest='send_report', type=bool, default=False)
def audit_s3(accounts, send_report):
  """ Runs auditors/s3 """
  sm_audit_s3(accounts, send_report)


@manager.option('-a', '--accounts', dest='accounts', type=unicode, default=u'all')
@manager.option('-r', '--send_report', dest='send_report', type=bool, default=False)
def audit_iamuser(accounts, send_report):
  """ Runs auditors/iam_user """
  sm_audit_iamuser(accounts, send_report)


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
