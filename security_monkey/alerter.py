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

from security_monkey import app
from security_monkey.common.jinja import get_jinja_env
from security_monkey.datastore import User
from security_monkey.common.utils.utils import send_email


def get_subject(has_issues, has_new_issue, has_unjustified_issue, account, watcher_str):
    if has_new_issue:
        return "NEW ISSUE - [{}] Changes in {}".format(account, watcher_str)
    elif has_issues and has_unjustified_issue:
        return "[{}] Changes w/existing issues in {}".format(account, watcher_str)
    elif has_issues and not has_unjustified_issue:
        return "[{}] Changes w/justified issues in {}".format(account, watcher_str)
    else:
        return "[{}] Changes in {}".format(account, watcher_str)


def report_content(content):
    jenv = get_jinja_env()
    template = jenv.get_template('jinja_change_email.html')
    body = template.render(content)
    # app.logger.info(body)
    return body


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
        users = User.query.filter(User.accounts.any(name=account)).filter(User.change_reports=='ALL').all()
        self.emails = [user.email for user in users]
        team_emails = app.config.get('SECURITY_TEAM_EMAIL')
        self.emails.extend(team_emails)

    def report(self):
        """
        Collect change summaries from watchers defined and send out an email
        """
        changed_watchers = [watcher_auditor[0] for watcher_auditor in self.watchers_auditors if watcher_auditor[0].is_changed()]
        has_issues = has_new_issue = has_unjustified_issue = False
        for watcher in changed_watchers:
            (has_issues, has_new_issue, has_unjustified_issue) = watcher.issues_found()
            if has_issues:
                users = User.query.filter(User.accounts.any(name=self.account)).filter(User.change_reports=='ISSUES').all()
                new_emails = [user.email for user in users]
                self.emails.extend(new_emails)
                break

        watcher_types = [watcher.index for watcher in changed_watchers]
        watcher_str = ', '.join(watcher_types)
        if len(changed_watchers) == 0:
            app.logger.info("Alerter: no changes found")
            return

        app.logger.info("Alerter: Found some changes in {}: {}".format(self.account, watcher_str))
        content = {u'watchers': changed_watchers}
        body = report_content(content)
        subject = get_subject(has_issues, has_new_issue, has_unjustified_issue, self.account, watcher_str)
        return send_email(subject=subject, recipients=self.emails, html=body)
