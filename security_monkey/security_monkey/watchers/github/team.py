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
.. module: security_monkey.watchers.github.team
    :platform: Unix
    :synopsis: Watcher for GitHub Organization Teams.


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


class GitHubTeam(Watcher):
    index = 'team'
    i_am_singular = 'team'
    i_am_plural = 'teams'
    account_type = 'GitHub'

    def __init__(self, accounts=None, debug=False):
        super(GitHubTeam, self).__init__(accounts=accounts, debug=debug)
        self.honor_ephemerals = True
        self.ephemeral_paths = []
        self.github_creds = get_github_creds(self.accounts)

    def slurp(self):
        @record_exception(source="{index}-watcher".format(index=self.index))
        def fetch_org_teams(**kwargs):
            account = Account.query.filter(Account.name == kwargs["account_name"]).first()

            item_list = []

            # Fetch teams:
            app.logger.debug("Fetching organization teams for: {}".format(account.identifier))
            teams = strip_url_fields(self.list_org_teams(account.identifier))

            for team in teams:
                item_list.append(GitHubTeamItem(
                    account=account.name,
                    name=team["name"],
                    arn="{}/team/{}".format(account.identifier, team["slug"]),
                    config=team,
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
            results = fetch_org_teams(**kwargs)
            if not results:
                return [], kwargs["exception_map"]

            return results

        items, exc = slurp_items(index=self.index)

        return items, exc

    def list_org_teams(self, org):
        headers = {
            'Authorization': 'token {}'.format(self.github_creds[org])
        }

        params = {
            "page": 1,
        }
        done = False

        teams = []

        while not done:
            url = "{}orgs/{}/teams".format(GITHUB_URL, org)
            result = requests.get(url, headers=headers, params=params)

            if result.status_code != 200:
                raise InvalidResponseCodeFromGitHubError(org, result.status_code)

            if not result.links.get("last"):
                done = True
            else:
                params["page"] += 1

            result_json = result.json()
            teams += result_json

        return teams


class GitHubTeamItem(ChangeItem):
    def __init__(self, account=None, name=None, arn=None, config=None, source_watcher=None):
        super(GitHubTeamItem, self).__init__(index=GitHubTeam.index,
                                             region="universal",
                                             account=account,
                                             name=name,
                                             arn=arn,
                                             new_config=config if config else {},
                                             source_watcher=source_watcher)
