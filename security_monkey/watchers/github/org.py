#     Copyright 2017 Netflix
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
.. module: security_monkey.watchers.github.org
    :platform: Unix
    :synopsis: Watcher for GitHub Organizations.


.. version:: $$VERSION$$
.. moduleauthor:: Mike Grima <mgrima@netflix.com>

"""
from security_monkey import app
from security_monkey.common.github.util import get_github_creds, iter_org, strip_url_fields
from security_monkey.datastore import Account
from security_monkey.decorators import record_exception
from security_monkey.exceptions import InvalidResponseCodeFromGitHubError
from security_monkey.watcher import Watcher, ChangeItem
import requests

GITHUB_URL = "https://api.github.com/"


class GitHubOrg(Watcher):
    index = 'organization'
    i_am_singular = 'organization'
    i_am_plural = 'organizations'
    account_type = 'GitHub'

    def __init__(self, accounts=None, debug=False):
        super(GitHubOrg, self).__init__(accounts=accounts, debug=debug)
        self.honor_ephemerals = True
        self.ephemeral_paths = [
            "disk_usage",
            "owned_private_repos",
            "public_repos",
            "total_private_repos",
            "private_gists",
            "public_gists",
            "followers",
            "following",
            "plan$*$filled_seats"
        ]
        self.github_creds = get_github_creds(self.accounts)

    def slurp(self):
        @record_exception(source="{index}-watcher".format(index=self.index))
        def fetch_org_details(**kwargs):
            item_list = []
            account = Account.query.filter(Account.name == kwargs["account_name"]).first()

            # Fetch the initial GitHub organization details:
            app.logger.debug("Fetching initial org details for: {}".format(account.identifier))
            org_details = strip_url_fields(self.get_org_details(account.identifier))

            # Now, fetch details about the users within the organization:
            app.logger.debug("Fetching members for: {}".format(account.identifier))
            members = self.list_org_members(account.identifier)
            org_details["members"] = sorted(members)

            app.logger.debug("Fetching owners for: {}".format(account.identifier))
            owners = self.list_org_members(account.identifier, role="admin")
            org_details["owners"] = sorted(owners)

            app.logger.debug("Fetching members without 2FA for: {}".format(account.identifier))
            no_twofa = self.list_org_members(account.identifier, twofa="2fa_disabled")
            org_details["no_2fa_members"] = sorted(no_twofa)

            # Fetch outside collabs:
            app.logger.debug("Fetching all outside collaborators for: {}".format(account.identifier))
            outside_collabs = self.list_org_outside_collabs(account.identifier)
            org_details["outside_collaborators"] = sorted(outside_collabs)

            # Fetch teams:
            app.logger.debug("Fetching all teams for: {}".format(account.identifier))
            teams = self.list_org_teams(account.identifier)
            org_details["teams"] = sorted(teams)

            item_list.append(GitHubOrgItem(
                account=account.name,
                name=account.identifier,
                arn=account.identifier,
                config=org_details,
                source_watcher=self
            ))

            return item_list, kwargs["exception_map"]

        @iter_org(orgs=self.accounts)
        def slurp_items(**kwargs):
            # Are we skipping this org?
            if self.check_ignore_list(kwargs["account_name"]):
                app.logger.debug("Skipping ignored account: {}".format(kwargs["account_name"]))
                return [], kwargs["exception_map"]

            # Exception handling complexities...
            results = fetch_org_details(**kwargs)
            if not results:
                return [], kwargs["exception_map"]

            return results

        items, exc = slurp_items(index=self.index)

        return items, exc

    def get_org_details(self, org):
        headers = {
            'Authorization': 'token {}'.format(self.github_creds[org])
        }

        url = "{}orgs/{}".format(GITHUB_URL, org)

        result = requests.get(url, headers=headers)

        if result.status_code != 200:
            raise InvalidResponseCodeFromGitHubError(org, result.status_code)

        return result.json()

    def list_org_members(self, org, role="all", twofa="all"):
        headers = {
            'Authorization': 'token {}'.format(self.github_creds[org])
        }

        params = {
            "page": 1,
            "role": role,
            "filter": twofa
        }
        done = False

        members = set()

        while not done:
            url = "{}orgs/{}/members".format(GITHUB_URL, org)
            result = requests.get(url, headers=headers, params=params)

            if result.status_code != 200:
                raise InvalidResponseCodeFromGitHubError(org, result.status_code)

            if not result.links.get("last"):
                done = True
            else:
                params["page"] += 1

            result_json = result.json()
            for member in result_json:
                members.add(member["login"])

        return list(members)

    def list_org_outside_collabs(self, org):
        headers = {
            'Authorization': 'token {}'.format(self.github_creds[org])
        }

        params = {
            "page": 1,
        }

        done = False
        collabs = set()
        url = "{}orgs/{}/outside_collaborators".format(GITHUB_URL, org)

        while not done:
            result = requests.get(url, headers=headers, params=params)

            if result.status_code != 200:
                raise InvalidResponseCodeFromGitHubError(org, result.status_code)

            if not result.links.get("last"):
                done = True
            else:
                params["page"] += 1

            result_json = result.json()
            for collab in result_json:
                collabs.add(collab["login"])

        return list(collabs)

    def list_org_teams(self, org):
        headers = {
            'Authorization': 'token {}'.format(self.github_creds[org])
        }

        params = {
            "page": 1,
        }

        done = False
        teams = set()
        url = "{}orgs/{}/teams".format(GITHUB_URL, org)

        while not done:
            result = requests.get(url, headers=headers, params=params)

            if result.status_code != 200:
                raise InvalidResponseCodeFromGitHubError(org, result.status_code)

            if not result.links.get("last"):
                done = True
            else:
                params["page"] += 1

            result_json = result.json()
            for team in result_json:
                teams.add(team["name"])

        return list(teams)


class GitHubOrgItem(ChangeItem):
    def __init__(self, account=None, name=None, arn=None, config=None, source_watcher=None):
        super(GitHubOrgItem, self).__init__(index=GitHubOrg.index,
                                            region="universal",
                                            account=account,
                                            name=name,
                                            arn=arn,
                                            new_config=config if config else {},
                                            source_watcher=source_watcher)
