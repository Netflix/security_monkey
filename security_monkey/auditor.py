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
.. module: security_monkey.auditor
    :platform: Unix
    :synopsis: This class is subclassed to add audit rules.

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com>

"""

import datastore

from security_monkey import app, db
from security_monkey.watcher import ChangeItem
from security_monkey.common.jinja import get_jinja_env
from security_monkey.datastore import User, AuditorSettings, Item, ItemAudit, Technology
from security_monkey.common.utils.utils import send_email

from sqlalchemy import and_

class Auditor(object):
    """
    This class (and subclasses really) run a number of rules against the configurations
    and look for any violations.  These violations are saved with the object and a report
    is made available via the Web UI and through email.
    """
    index = None          # Should be overridden
    i_am_singular = None  # Should be overridden
    i_am_plural = None    # Should be overridden

    def __init__(self, accounts=None, debug=False):
        self.datastore = datastore.Datastore()
        self.accounts = accounts
        self.debug = debug
        self.items = []
        self.team_emails = app.config.get('SECURITY_TEAM_EMAIL')
        self.emails = []
        self.emails.extend(self.team_emails)

        for account in self.accounts:
            users = User.query.filter(User.daily_audit_email==True).filter(User.accounts.any(name=account)).all()

        self.emails.extend([user.email for user in users])

    def add_issue(self, score, issue, item, notes=None):
        """
        Adds a new issue to an item, if not already reported.
        :return: The new issue
        """

        if notes and len(notes) > 512:
            notes = notes[0:512]

        for existing_issue in item.audit_issues:
            if existing_issue.issue == issue:
                if existing_issue.notes == notes:
                    if existing_issue.score == score:
                        app.logger.debug(
                            "Not adding issue because it was already found:{}/{}/{}/{}\n\t{} -- {}"
                            .format(item.index, item.region, item.account, item.name, issue, notes))
                        return existing_issue

        app.logger.debug("Adding issue: {}/{}/{}/{}\n\t{} -- {}"
                         .format(item.index, item.region, item.account, item.name, issue, notes))
        new_issue = datastore.ItemAudit(score=score,
                                        issue=issue,
                                        notes=notes,
                                        justified=False,
                                        justified_user_id=None,
                                        justified_date=None,
                                        justification=None)

        item.audit_issues.append(new_issue)
        return new_issue

    def prep_for_audit(self):
        """
        To be overridden by child classes who
        need a way to prepare for the next run.
        """
        pass

    def audit_these_objects(self, items):
        """
        Only inspect the given items.
        """
        app.logger.debug("Asked to audit {} Objects".format(len(items)))
        self.prep_for_audit()
        methods = [getattr(self, method_name) for method_name in dir(self) if method_name.find("check_") == 0]
        app.logger.debug("methods: {}".format(methods))
        for item in items:
            for method in methods:
                method(item)
        self.items = items

    def audit_all_objects(self):
        """
        Read all items from the database and inspect them all.
        """
        self.items = self.read_previous_items()
        self.audit_these_objects(self.items)

    def read_previous_items(self):
        """
        Pulls the last-recorded configuration from the database.
        :return: List of all items for the given technology and the given account.
        """
        prev_list = []
        for account in self.accounts:
            prev = self.datastore.get_all_ctype_filtered(tech=self.index, account=account, include_inactive=False)
            # Returns a map of {Item: ItemRevision}
            for item in prev:
                item_revision = prev[item]
                new_item = ChangeItem(index=self.index,
                                      region=item.region,
                                      account=item.account.name,
                                      name=item.name,
                                      new_config=item_revision.config)
                new_item.audit_issues.extend(item.issues)
                new_item.audit_issues = []
                new_item.db_item = item
                prev_list.append(new_item)
        return prev_list

    def save_issues(self):
        """
        Save all new issues.  Delete all fixed issues.
        """
        app.logger.debug("\n\nSaving Issues.")
        for item in self.items:
            if not hasattr(item, 'db_item'):
                item.db_item = self.datastore._get_item(item.index, item.region, item.account, item.name)

            existing_issues = item.db_item.issues
            new_issues = item.audit_issues

            # Add new issues
            for new_issue in new_issues:
                nk = "{} -- {}".format(new_issue.issue, new_issue.notes)
                if nk not in ["{} -- {}".format(old_issue.issue, old_issue.notes) for old_issue in existing_issues]:
                    app.logger.debug("Saving NEW issue {}".format(nk))
                    item.found_new_issue = True
                    item.confirmed_new_issues.append(new_issue)
                    item.db_item.issues.append(new_issue)
                    db.session.add(item.db_item)
                    db.session.add(new_issue)
                else:
                    for issue in existing_issues:
                        if issue.issue == new_issue.issue and issue.notes == new_issue.notes:
                            item.confirmed_existing_issues.append(issue)
                            break
                    key = "{}/{}/{}/{}".format(item.index, item.region, item.account, item.name)
                    app.logger.debug("Issue was previously found. Not overwriting.\n\t{}\n\t{}".format(key, nk))

            # Delete old issues
            for old_issue in existing_issues:
                ok = "{} -- {}".format(old_issue.issue, old_issue.notes)
                if ok not in ["{} -- {}".format(new_issue.issue, new_issue.notes) for new_issue in new_issues]:
                    app.logger.debug("Deleting FIXED issue {}".format(ok))
                    item.confirmed_fixed_issues.append(old_issue)
                    db.session.delete(old_issue)

        db.session.commit()
        self._create_auditor_settings()

    def email_report(self, report):
        """
        Given a report, send an email using SES.
        """
        if not report:
            app.logger.info("No Audit issues.  Not sending audit email.")
            return

        subject = "Security Monkey {} Auditor Report".format(self.i_am_singular)
        send_email(subject=subject, recipients=self.emails, html=report)

    def create_report(self):
        """
        Using a Jinja template (jinja_audit_email.html), create a report that can be emailed.
        :return: HTML - The output of the rendered template.
        """
        jenv = get_jinja_env()
        template = jenv.get_template('jinja_audit_email.html')
        # This template expects a list of items that have been sorted by total score in
        # decending order.
        for item in self.items:
            item.totalscore = 0
            for issue in item.audit_issues:
                item.totalscore = item.totalscore + issue.score
        sorted_list = sorted(self.items, key=lambda item: item.totalscore)
        sorted_list.reverse()
        report_list = []
        for item in sorted_list:
            if item.totalscore > 0:
                report_list.append(item)
            else:
                break
        if len(report_list) > 0:
            return template.render({'items': report_list})
        else:
            return False

    def _create_auditor_settings(self):
        """
        Checks to see if an AuditorSettings entry exists for each issue.
        If it does not, one will be created with disabled set to false.
        """
        app.logger.debug("Creating/Assigning Auditor Settings in account {} and tech {}".format(self.accounts, self.index))

        query = ItemAudit.query
        query = query.join((Item, Item.id == ItemAudit.item_id))
        query = query.join((Technology, Technology.id == Item.tech_id))
        query = query.filter(Technology.name == self.index)
        issues = query.filter(ItemAudit.auditor_setting_id == None).all()

        for issue in issues:
            self._set_auditor_setting_for_issue(issue)

        db.session.commit()
        app.logger.debug("Done Creating/Assigning Auditor Settings in account {} and tech {}".format(self.accounts, self.index))

    def _set_auditor_setting_for_issue(self, issue):

        auditor_setting = AuditorSettings.query.filter(
            and_(
                AuditorSettings.tech_id == issue.item.tech_id,
                AuditorSettings.account_id == issue.item.account_id,
                AuditorSettings.issue_text == issue.issue
            )
        ).first()

        if auditor_setting:
            auditor_setting.issues.append(issue)
            db.session.add(auditor_setting)
            return auditor_setting

        auditor_setting = AuditorSettings(
            tech_id=issue.item.tech_id,
            account_id=issue.item.account_id,
            disabled=False,
            issue_text=issue.issue
        )

        auditor_setting.issues.append(issue)
        db.session.add(auditor_setting)
        db.session.commit()
        db.session.refresh(auditor_setting)

        app.logger.debug("Created AuditorSetting: {} - {} - {}".format(
            issue.issue,
            self.index,
            issue.item.account.name))

        return auditor_setting