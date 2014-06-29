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
"""
.. module: security_monkey.reporter
    :platform: Unix
    :synopsis: Runs all change watchers and auditors and uses the alerter
    to send emails for a specific account.
    
.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

from security_monkey.watchers.sns import SNS
from security_monkey.auditors.sns import SNSAuditor
from security_monkey.watchers.sqs import SQS
from security_monkey.watchers.keypair import Keypair
from security_monkey.watchers.iam_role import IAMRole
from security_monkey.watchers.iam_group import IAMGroup
from security_monkey.watchers.iam_user import IAMUser
from security_monkey.auditors.iam_user import IAMUserAuditor
from security_monkey.watchers.security_group import SecurityGroup
from security_monkey.auditors.security_group import SecurityGroupAuditor
from security_monkey.watchers.rds_security_group import RDSSecurityGroup
from security_monkey.auditors.rds_security_group import RDSSecurityGroupAuditor
from security_monkey.watchers.s3 import S3
from security_monkey.auditors.s3 import S3Auditor
from security_monkey.watchers.elb import ELB
from security_monkey.watchers.iam_ssl import IAMSSL

from security_monkey.alerter import Alerter
from security_monkey import app, db

import json
import time

class Reporter(object):
    """Sets up all watchers and auditors and the alerters"""

    def __init__(self, accounts=None, alert_accounts=None, debug=False):
        self.account_watchers = {}
        self.account_alerters = {}
        if not alert_accounts:
            alert_accounts = accounts
        for account in accounts:
            self.account_watchers[account] = [
                (SQS(accounts=[account], debug=debug), None),
                (ELB(accounts=[account], debug=debug), None),
                (IAMSSL(accounts=[account], debug=debug), None),
                (RDSSecurityGroup(accounts=[account], debug=debug), RDSSecurityGroupAuditor(accounts=[account], debug=debug)),
                (SecurityGroup(accounts=[account], debug=debug), SecurityGroupAuditor(accounts=[account], debug=debug)),
                (S3(accounts=[account], debug=debug), S3Auditor(accounts=[account], debug=debug)),
                (IAMUser(accounts=[account], debug=debug), IAMUserAuditor(accounts=[account], debug=debug)),
                (IAMGroup(accounts=[account], debug=debug), None), 
                (IAMRole(accounts=[account], debug=debug), None), 
                (Keypair(accounts=[account], debug=debug), None),
                (SNS(accounts=[account], debug=debug), SNSAuditor(accounts=[account], debug=debug))
            ]
            if account in alert_accounts:
                self.account_alerters[account] = Alerter(watchers_auditors=self.account_watchers[account], account=account)

    def run(self, account):
        """Starts the process of watchers -> auditors -> alerters -> watchers.save()"""
        app.logger.info("Starting work on account {}.".format(account))
        time1 = time.time()        
        for (watcher, auditor) in self.account_watchers[account]:
            (items, exception_map) = watcher.slurp()
            watcher.find_changes(current=items, exception_map=exception_map)
            items_to_audit = [item for item in watcher.created_items + watcher.changed_items]

            if len(items_to_audit) > 0 and auditor is not None:
                auditor.audit_these_objects(items_to_audit)
            
            watcher.save()
            if auditor is not None:
                auditor.save_issues()
                
            app.logger.info("Account {} is done with {}".format(account, watcher.i_am_singular))

        time2 = time.time()
        app.logger.info('Run Account %s took %0.1f s' % (account, (time2-time1)))

        if account in self.account_alerters:
            self.account_alerters[account].report()
            
        db.session.close()
