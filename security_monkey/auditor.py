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
from security_monkey.datastore import User, AuditorSettings, Item, ItemAudit, Technology, Account, ItemAuditScore, AccountPatternAuditScore
from security_monkey.common.utils import send_email
from security_monkey.account_manager import get_account_by_name

from sqlalchemy import and_
from collections import defaultdict

auditor_registry = defaultdict(list)

class AuditorType(type):
    def __init__(cls, name, bases, attrs):
        super(AuditorType, cls).__init__(name, bases, attrs)
        if cls.__name__ != 'Auditor' and cls.index:
            # Only want to register auditors explicitly loaded by find_modules
            if not '.' in cls.__module__:
                found = False
                for auditor in auditor_registry[cls.index]:
                    if auditor.__module__ == cls.__module__ and auditor.__name__ == cls.__name__:
                        found = True
                        break
                if not found:
                    app.logger.debug("Registering auditor {} {}.{}".format(cls.index, cls.__module__, cls.__name__))
                    auditor_registry[cls.index].append(cls)

class Auditor(object):
    """
    This class (and subclasses really) run a number of rules against the configurations
    and look for any violations.  These violations are saved with the object and a report
    is made available via the Web UI and through email.
    """
    index = None          # Should be overridden
    i_am_singular = None  # Should be overridden
    i_am_plural = None    # Should be overridden
    __metaclass__ = AuditorType
    support_auditor_indexes = []
    support_watcher_indexes = []

    def __init__(self, accounts=None, debug=False):
        self.datastore = datastore.Datastore()
        self.accounts = accounts
        self.debug = debug
        self.items = []
        self.team_emails = app.config.get('SECURITY_TEAM_EMAIL', [])
        self.emails = []
        self.current_support_items = {}
        self.override_scores = None
        self.current_method_name = None

        if type(self.team_emails) in (str, unicode):
            self.emails.append(self.team_emails)
        elif type(self.team_emails) in (list, tuple):
            self.emails.extend(self.team_emails)
        else:
            app.logger.info("Auditor: SECURITY_TEAM_EMAIL contains an invalid type")

        for account in self.accounts:
            users = User.query.filter(User.daily_audit_email==True).filter(User.accounts.any(name=account)).all()
            self.emails.extend([user.email for user in users])

    def add_issue(self, score, issue, item, notes=None):
        """
        Adds a new issue to an item, if not already reported.
        :return: The new issue
        """

        if notes and len(notes) > 1024:
            notes = notes[0:1024]

        if not self.override_scores:
            query = ItemAuditScore.query.filter(ItemAuditScore.technology == self.index)
            self.override_scores = query.all()

        # Check for override scores to apply
        score = self._check_for_override_score(score, item.account)

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
        self.current_support_items = {}
        query = ItemAuditScore.query.filter(ItemAuditScore.technology == self.index)
        self.override_scores = query.all()

        methods = [getattr(self, method_name) for method_name in dir(self) if method_name.find("check_") == 0]
        app.logger.debug("methods: {}".format(methods))
        for item in items:
            for method in methods:
                self.current_method_name = method.func_name
                # If the check function is disabled by an entry on Settings/Audit Issue Scores
                # the function will not be run and any previous issues will be cleared
                if not self._is_current_method_disabled():
                    method(item)
        self.items = items

        self.override_scores = None

    def _is_current_method_disabled(self):
        """
        Determines whether this method has been marked as disabled based on Audit Issue Scores
        settings.
        """
        for override_score in self.override_scores:
            if override_score.method == self.current_method_name + ' (' + self.__class__.__name__ + ')':
                return override_score.disabled

        return False


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
                                      arn=item.arn,
                                      new_config=item_revision.config)
                new_item.audit_issues = []
                new_item.db_item = item
                prev_list.append(new_item)
        return prev_list

    def read_previous_items_for_account(self, index, account):
        """
        Pulls the last-recorded configuration from the database.
        :return: List of all items for the given technology and the given account.
        """
        prev_list = []
        prev = self.datastore.get_all_ctype_filtered(tech=index, account=account, include_inactive=False)
        # Returns a map of {Item: ItemRevision}
        for item in prev:
            item_revision = prev[item]
            new_item = ChangeItem(index=self.index,
                                  region=item.region,
                                  account=item.account.name,
                                  name=item.name,
                                  arn=item.arn,
                                  new_config=item_revision.config)
            new_item.audit_issues = []
            new_item.db_item = item
            prev_list.append(new_item)

        return prev_list

    def save_issues(self):
        """
        Save all new issues.  Delete all fixed issues.
        """
        app.logger.debug("\n\nSaving Issues.")

        # Work around for issue where previous get's may cause commit to fail
        db.session.rollback()
        for item in self.items:
            changes = False
            loaded = False
            if not hasattr(item, 'db_item'):
                loaded = True
                item.db_item = self.datastore._get_item(item.index, item.region, item.account, item.name)

            existing_issues = list(item.db_item.issues)
            new_issues = item.audit_issues

            for issue in item.db_item.issues:
                if not issue.auditor_setting:
                    self._set_auditor_setting_for_issue(issue)

            # Add new issues
            old_scored = ["{} -- {} -- {} -- {} -- {}".format(
                            old_issue.auditor_setting.auditor_class,
                            old_issue.issue,
                            old_issue.notes,
                            old_issue.score,
                            self._item_list_string(old_issue)) for old_issue in existing_issues]

            for new_issue in new_issues:
                nk = "{} -- {} -- {} -- {} -- {}".format(self.__class__.__name__,
                        new_issue.issue,
                        new_issue.notes,
                        new_issue.score,
                        self._item_list_string(new_issue))

                if nk not in old_scored:
                    changes = True
                    app.logger.debug("Saving NEW issue {}".format(nk))
                    item.found_new_issue = True
                    item.confirmed_new_issues.append(new_issue)
                    item.db_item.issues.append(new_issue)
                else:
                    for issue in existing_issues:
                        if issue.issue == new_issue.issue and issue.notes == new_issue.notes and issue.score == new_issue.score:
                            item.confirmed_existing_issues.append(issue)
                            break
                    key = "{}/{}/{}/{}".format(item.index, item.region, item.account, item.name)
                    app.logger.debug("Issue was previously found. Not overwriting.\n\t{}\n\t{}".format(key, nk))

            # Delete old issues
            new_scored = ["{} -- {} -- {} -- {}".format(new_issue.issue,
                                new_issue.notes,
                                new_issue.score,
                                self._item_list_string(new_issue)) for new_issue in new_issues]

            for old_issue in existing_issues:
                ok = "{} -- {} -- {} -- {}".format(old_issue.issue,
                        old_issue.notes,
                        old_issue.score,
                        self._item_list_string(old_issue))

                old_issue_class = old_issue.auditor_setting.auditor_class
                if old_issue_class is None or (old_issue_class == self.__class__.__name__ and ok not in new_scored):
                    changes = True
                    app.logger.debug("Deleting FIXED or REPLACED issue {}".format(ok))
                    item.confirmed_fixed_issues.append(old_issue)
                    item.db_item.issues.remove(old_issue)

            if changes:
                db.session.add(item.db_item)
            else:
                if loaded:
                    db.session.expunge(item.db_item)

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
        # descending order.
        for item in self.items:
            item.totalscore = 0
            for issue in item.db_item.issues:
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

    def applies_to_account(self, account):
        """
        Placeholder for custom auditors which may only want to run against
        certain types of accounts
        """
        return True

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
                AuditorSettings.issue_text == issue.issue,
                AuditorSettings.auditor_class == self.__class__.__name__
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
            issue_text=issue.issue,
            auditor_class=self.__class__.__name__
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

    def _check_cross_account(self, src_account_number, dest_item, location):
        account = Account.query.filter(Account.identifier == src_account_number).first()
        account_name = None
        if account is not None:
            account_name = account.name

        src = account_name or src_account_number
        dst = dest_item.account

        if src == dst:
            return None

        notes = "SRC [{}] DST [{}]. Location: {}".format(src, dst, location)

        if not account_name:
            tag = "Unknown Cross Account Access"
            self.add_issue(10, tag, dest_item, notes=notes)
        elif account_name != dest_item.account and not account.third_party:
            tag = "Friendly Cross Account Access"
            self.add_issue(0, tag, dest_item, notes=notes)
        elif account_name != dest_item.account and account.third_party:
            tag = "Friendly Third Party Cross Account Access"
            self.add_issue(0, tag, dest_item, notes=notes)

    def _check_cross_account_root(self, source_item, dest_arn, actions):
        if not actions:
            return None

        account = Account.query.filter(Account.name == source_item.account).first()
        source_item_account_number = account.identifier

        if source_item_account_number == dest_arn.account_number:
            return None

        tag = "Cross-Account Root IAM"
        notes = "ALL IAM Roles/users/groups in account {} can perform the following actions:\n"\
            .format(dest_arn.account_number)
        notes += "{}".format(actions)
        self.add_issue(6, tag, source_item, notes=notes)

    def get_auditor_support_items(self, auditor_index, account):
        for index in self.support_auditor_indexes:
            if index == auditor_index:
                audited_items = self.current_support_items.get(account + auditor_index)
                if audited_items is None:
                    audited_items = self.read_previous_items_for_account(auditor_index, account)
                    if not audited_items:
                        app.logger.info("{} Could not load audited items for {}/{}".format(self.index, auditor_index, account))
                        self.current_support_items[account+auditor_index] = []
                    else:
                        self.current_support_items[account+auditor_index] = audited_items
                return audited_items

        raise Exception("Auditor {} is not configured as an audit support auditor for {}".format(auditor_index, self.index))

    def get_watcher_support_items(self, watcher_index, account):
        for index in self.support_watcher_indexes:
            if index == watcher_index:
                items = self.current_support_items.get(account + watcher_index)
                if items is None:
                    items = self.read_previous_items_for_account(watcher_index, account)
                    # Only the item contents should be used for watcher support
                    # config. This prevents potentially stale issues from being
                    # used by the auditor
                    for item in items:
                        item.db_item.issues = []

                    if not items:
                        app.logger.info("{} Could not load support items for {}/{}".format(self.index, watcher_index, account))
                        self.current_support_items[account+watcher_index] = []
                    else:
                        self.current_support_items[account+watcher_index] = items
                return items

        raise Exception("Watcher {} is not configured as a data support watcher for {}".format(watcher_index, self.index))

    def link_to_support_item_issues(self, item, sub_item, sub_issue_message=None, issue_message=None, issue=None, score=None):
        """
        Creates a new issue that is linked to an issue in a support auditor
        """
        matching_issues = []
        for sub_issue in sub_item.issues:
            if not sub_issue_message or sub_issue.issue == sub_issue_message:
                matching_issues.append(sub_issue)

        if len(matching_issues) > 0:
            for matching_issue in matching_issues:
                if issue is None:
                    if issue_message is None:
                        if sub_issue_message is not None:
                            issue_message = sub_issue_message
                        else:
                            issue_message = "UNDEFINED"

                    if score is not None:
                       issue = self.add_issue(score, issue_message, item)
                    else:
                       issue = self.add_issue(matching_issue.score, issue_message, item)
                else:
                    if score is not None:
                        issue.score = score
                    else:
                        issue.score = issue.score + matching_issue.score

            issue.sub_items.append(sub_item)

        return issue

    def link_to_support_item(self, score, issue_message, item, sub_item, issue=None):
        """
        Creates a new issue that is linked a support watcher item
        """
        if issue is None:
            issue = self.add_issue(score, issue_message, item)
        issue.sub_items.append(sub_item)
        return issue

    def _item_list_string(self, issue):
        """
        Use by save_issue to generate a unique id for an item
        """
        item_ids = []
        for sub_item in issue.sub_items:
            item_ids.append(sub_item.id)

        item_ids.sort()
        return str(item_ids)

    def _check_for_override_score(self, score, account):
        """
        Return an override to the hard coded score for an issue being added. This could either
        be a general override score for this check method or one that is specific to a particular
        field in the account.

        :param score: the hard coded score which will be returned back if there is
               no applicable override
        :param account: The account name, used to look up the value of any pattern
               based overrides
        :return:
        """
        for override_score in self.override_scores:
            # Look for an oberride entry that applies to
            if override_score.method == self.current_method_name + ' (' + self.__class__.__name__ + ')':
                # Check for account pattern override where a field in the account matches
                # one configured in Settings/Audit Issue Scores
                account = get_account_by_name(account)
                for account_pattern_score in override_score.account_pattern_scores:
                    if getattr(account, account_pattern_score.account_field, None):
                        # Standard account field, such as identifier or notes
                        account_pattern_value = getattr(account, account_pattern_score.account_field)
                    else:
                        # If there is no attribute, this is an account custom field
                        account_pattern_value = account.getCustom(account_pattern_score.account_field)

                    if account_pattern_value is not None:
                        # Override the score based on the matching pattern
                        if account_pattern_value == account_pattern_score.account_pattern:
                            app.logger.debug("Overriding score based on config {}:{} {}/{}".format(self.index, self.current_method_name + '(' + self.__class__.__name__ + ')', score, account_pattern_score.score))
                            score = account_pattern_score.score
                            break
                else:
                    # No specific override pattern fund. use the generic override score
                    app.logger.debug("Overriding score based on config {}:{} {}/{}".format(self.index, self.current_method_name + '(' + self.__class__.__name__ + ')', score, override_score.score))
                    score = override_score.score

        return score
