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
.. module: security_monkey.alerter
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netfilx.com> @monkeysecurity

"""

import boto

from security_monkey import app
from security_monkey.common.sts_connect import connect
from security_monkey.common.jinja import get_jinja_env
from security_monkey.datastore import User, Account


class Alerter(object):

    def __init__(self, watchers_auditors=[], account=None, debug=False):
        """
        envs are list of environments where we care about changes
        """

        self.account = account
        self.notifications = ""
        self.new = []
        self.delete = []
        self.changed = []
        self.watchers_auditors = watchers_auditors
        self.from_address = app.config.get('DEFAULT_MAIL_SENDER')

        users = User.query.filter(User.accounts.any(name=account)).all()
        self.emails = [user.email for user in users]
        team_email = app.config.get('SECURITY_TEAM_EMAIL')
        self.emails.extend(team_email)


    def report(self):
        """
        Collect change summaries from watchers defined and send out an email
        """
        changed_watchers = [watcher_auditor[0] for watcher_auditor in self.watchers_auditors if watcher_auditor[0].is_changed()]
        watcher_types = [watcher.index for watcher in changed_watchers]
        watcher_str = ', '.join(watcher_types)
        if len(changed_watchers) == 0:
            app.logger.info("Alerter: no changes found")
            return
        app.logger.info("Alerter: Found some changes in {}: {}".format(self.account, watcher_str))
        content = {u'watchers': changed_watchers}
        body = self.report_content(content)
        return self.mail(body, watcher_str)

    def report_content(self, content):
        jenv = get_jinja_env()
        template = jenv.get_template('jinja_change_email.html')
        body = template.render(content)
        #app.logger.info(body)
        return body

    def mail(self, body, watcher_type):
        ses = boto.connect_ses()
        for email in self.emails:
            try:
                subject = "[{}] Changes in {}".format(self.account, watcher_type)
                ses.send_email(self.from_address, subject, body,  email, format="html")
                app.logger.debug("Emailed {} - {} ".format(email, subject))
            except Exception, e:
                m = "Failed to send failure message: {} {}".format(Exception, e)
                app.logger.debug(m)
