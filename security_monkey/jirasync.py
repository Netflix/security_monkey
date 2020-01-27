"""
.. module: security_monkey.jirasync
    :platform: Unix
    :synopsis: Creates and updates JIRA tickets based on current issues

.. version:: $$VERSION$$
.. moduleauthor:: Quentin Long <qlo@yelp.com>

"""
import datetime
import re
import time
import urllib.request, urllib.parse, urllib.error
import yaml

from jira.client import JIRA

from security_monkey.datastore import Account, Technology, AuditorSettings
from security_monkey import app


class JiraSync(object):
    """ Syncs auditor issues with JIRA tickets. """
    def __init__(self, jira_file):
        try:
            with open(jira_file) as jf:
                data = jf.read()
                data = yaml.safe_load(data)
                self.account = data['account']
                self.password = data['password']
                self.project = data['project']
                self.server = data['server']
                self.issue_type = data['issue_type']
                self.url = data['url']
                self.ip_proxy = data.get('ip_proxy')
                self.port_proxy = data.get('port_proxy')
                self.disable_transitions = data.get('disable_transitions', False)
                self.assignee = data.get('assignee', None)
                self.only_update_on_change = data.get('only_update_on_change', False)
        except KeyError as e:
            raise Exception('JIRA sync configuration missing required field: {}'.format(e))
        except IOError as e:
            raise Exception('Error opening JIRA sync configuration file: {}'.format(e))
        except yaml.scanner.ScannerError as e:
            raise Exception('JIRA sync configuration file contains malformed YAML: {}'.format(e))

        try:
            options = {}
            options['verify'] = app.config.get('JIRA_SSL_VERIFY', True)

            proxies = None
            if (self.ip_proxy and self.port_proxy):
                proxy_connect = '{}:{}'.format(self.ip_proxy, self.port_proxy)
                proxies = {'http': proxy_connect, 'https': proxy_connect}
            elif (self.ip_proxy and self.port_proxy is None):
                app.logger.warn("Proxy host set, but not proxy port.  Skipping JIRA proxy settings.")
            elif (self.ip_proxy is None and self.port_proxy):
                app.logger.warn("Proxy port set, but not proxy host.  Skipping JIRA proxy settings.")

            self.client = JIRA(self.server, basic_auth=(self.account, self.password), options=options, proxies=proxies)  # pylint: disable=E1123

        except Exception as e:
            raise Exception("Error connecting to JIRA: {}".format(str(e)[:1024]))

    def close_issue(self, issue):
        try:
            self.transition_issue(issue, app.config.get('JIRA_CLOSED', 'Closed'))
        except Exception as e:
            app.logger.error('Error closing issue {} ({}): {}'.format(issue.fields.summary, issue.key, e))

    def open_issue(self, issue):
        try:
            self.transition_issue(issue, app.config.get('JIRA_OPEN', 'Open'))
        except Exception as e:
            app.logger.error('Error opening issue {} ({}): {}'.format(issue.fields.summary, issue.key, e))

    def transition_issue(self, issue, transition_name):
        transitions = self.client.transitions(issue)
        for transition in transitions:
            if transition['name'].lower() == transition_name.lower():
                break
        else:
            app.logger.error('No transition {} for issue {}'.format(transition_name, issue.key))
            return
        self.client.transition_issue(issue, transition['id'])

    def add_or_update_issue(self, issue, technology, account, count):
        """ Searches for existing tickets based on the summary. If one exists,
        it will update the count and preserve any leading description text. If not, it will create a ticket. """
        summary = '{0} - {1} - {2}'.format(issue, technology, account)
        # Having dashes in JQL cuases it to return no results
        summary_search = summary.replace('- ', '')
        jql = 'project={0} and summary~"{1}"'.format(self.project, summary_search)
        issues = self.client.search_issues(jql)

        url = "{0}/#/issues/-/{1}/{2}/-/-/-/True/{3}/1/25".format(self.url, technology, account, urllib.parse.quote(issue, ''))
        timezone = time.tzname[time.localtime().tm_isdst]
        description = ("This ticket was automatically created by Security Monkey. DO NOT EDIT SUMMARY OR BELOW THIS LINE\n"
                      "Number of issues: {0}\n"
                      "Account: {1}\n"
                      "[View on Security Monkey|{2}]\n"
                      "Last updated: {3} {4}".format(count, account, url, datetime.datetime.now().isoformat(), timezone))

        for issue in issues:
            # Make sure we found the exact ticket
            if issue.fields.summary == summary:
                old_desc = issue.fields.description
                old_desc = old_desc[:old_desc.find('This ticket was automatically created by Security Monkey')]
                if self.only_update_on_change and issue.fields.description:
                    old_count = re.search("Number of issues: (\d*)\\n", issue.fields.description).group(1)
                    if int(old_count) != count:
                        # The count has changed so it still needs to be updated
                        issue.update(description=old_desc + description)
                        app.logger.debug("Updated issue {} ({})".format(summary, issue.key))
                    else:
                        # The count hasn't changed so it will not be updated
                        app.logger.debug('Not updating issue, configured to only update if the count has changed.')
                else:
                    issue.update(description=old_desc + description)
                    app.logger.debug("Updated issue {} ({})".format(summary, issue.key))

                if self.disable_transitions:
                    return

                if issue.fields.status.name == app.config.get('JIRA_CLOSED', 'Closed') and count:
                    self.open_issue(issue)
                    app.logger.debug("Reopened issue {} ({})".format(summary, issue.key))
                elif issue.fields.status.name != app.config.get('JIRA_CLOSED', 'Closed') and count == 0:
                    self.close_issue(issue)
                    app.logger.debug("Closed issue {} ({})".format(summary, issue.key))
                return

        # Don't open a ticket with no issues
        if count == 0:
            return

        jira_args = {'project': {'key': self.project},
                     'issuetype': {'name': self.issue_type},
                     'summary': summary,
                     'description': description}

        if self.assignee is not None:
            jira_args['assignee'] = {'name': self.assignee}

        try:
            issue = self.client.create_issue(**jira_args)
            app.logger.debug("Created issue {} ({})".format(summary, issue.key))
        except Exception as e:
            app.logger.error("Error creating issue {}: {}".format(summary, e))

    def sync_issues(self, accounts=None, tech_name=None):
        """ Runs add_or_update_issue for every AuditorSetting, filtered by technology
        and accounts, if provided. """
        query = AuditorSettings.query.join(
            (Technology, Technology.id == AuditorSettings.tech_id)
        ).join(
            (Account, Account.id == AuditorSettings.account_id)
        ).filter(
            (AuditorSettings.disabled == False)
        )
        if accounts:
            query = query.filter(Account.name.in_(accounts))
        if tech_name:
            query = query.filter(Technology.name == tech_name)

        for auditorsetting in query.all():
            unjustified = [issue for issue in auditorsetting.issues if not issue.justified]
            self.add_or_update_issue(auditorsetting.issue_text,
                                     auditorsetting.technology.name,
                                     auditorsetting.account.name,
                                     len(unjustified))
