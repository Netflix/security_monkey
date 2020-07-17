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
from six import string_types

from security_monkey import app
from security_monkey.common.jinja import get_jinja_env
from security_monkey.datastore import User
from security_monkey.common.utils import send_email


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

    def __init__(self, watchers_auditors=None, account=None, debug=False):
        """
        envs are list of environments where we care about changes
        """
        self.account = account
        self.notifications = ""
        self.new = []
        self.delete = []
        self.changed = []
        self.watchers_auditors = watchers_auditors if watchers_auditors else []
        users = User.query.filter(User.accounts.any(name=account)).filter(User.change_reports == 'ALL')\
            .filter(User.active == True).all()  # noqa
        self.emails = [user.email for user in users]
        self.team_emails = app.config.get('SECURITY_TEAM_EMAIL', [])

        if isinstance(self.team_emails, string_types):
            self.emails.append(self.team_emails)
        elif isinstance(self.team_emails, (list, tuple)):
            self.emails.extend(self.team_emails)
        else:
            app.logger.info("Alerter: SECURITY_TEAM_EMAIL contains an invalid type")

    def report(self):
        """
        Collect change summaries from watchers defined and send out an email
        """
        if app.config.get("DISABLE_EMAILS"):
            app.logger.info("Alerter is not sending emails as they are disabled in the Security Monkey configuration.")
            return

        changed_watchers = [watcher_auditor.watcher
                            for watcher_auditor in self.watchers_auditors if watcher_auditor.watcher.is_changed()]
        has_issues = has_new_issue = has_unjustified_issue = False
        for watcher in changed_watchers:
            (has_issues, has_new_issue, has_unjustified_issue) = watcher.issues_found()
            if has_issues:
                users = User.query.filter(
                    User.accounts.any(name=self.account)).filter(User.change_reports == 'ISSUES').filter(User.active == True).all()  # noqa
                new_emails = [user.email for user in users]
                self.emails.extend(new_emails)
                break

        watcher_types = [watcher.index for watcher in changed_watchers]
        watcher_str = ', '.join(watcher_types)
        if len(changed_watchers) == 0:
            app.logger.info("Alerter: no changes found")
            return

        app.logger.info("Alerter: Found some changes in {}: {}".format(self.account, watcher_str))
        content = {'watchers': changed_watchers}
        body = report_content(content)
        subject = get_subject(has_issues, has_new_issue, has_unjustified_issue, self.account, watcher_str)
        return send_email(subject=subject, recipients=self.emails, html=body)
