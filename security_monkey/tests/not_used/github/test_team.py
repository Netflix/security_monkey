#     Copyright 2017 Netflix, Inc.
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
.. module: security_monkey.tests.watchers.github.test_team
    :platform: Unix
.. version:: $$VERSION$$
.. moduleauthor::  Mike Grima <mgrima@netflix.com>
"""
import json

from security_monkey import app
from security_monkey.datastore import Account, Technology, AccountType, ExceptionLogs
from security_monkey.exceptions import InvalidResponseCodeFromGitHubError
from security_monkey.tests import SecurityMonkeyTestCase, db

import mock

TEAMS_PAGE_ONE = """[
    {
        "id": 1,
        "url": "https://api.github.com/teams/1",
        "name": "Justice League",
        "slug": "justice-league",
        "description": "A great team.",
        "privacy": "closed",
        "permission": "admin",
        "members_url": "https://api.github.com/teams/1/members{/member}",
        "repositories_url": "https://api.github.com/teams/1/repos"
    }
]"""

TEAMS_PAGE_TWO = """[
    {
        "id": 2,
        "url": "https://api.github.com/teams/2",
        "name": "Team2",
        "slug": "Team2",
        "description": "A great team.",
        "privacy": "closed",
        "permission": "admin",
        "members_url": "https://api.github.com/teams/2/members{/member}",
        "repositories_url": "https://api.github.com/teams/2/repos"
    }
]"""


class MockTeamList:
    def __init__(self, status_code, page):
        if page == 1:
            self.json_data = TEAMS_PAGE_ONE
            self.links = {"last": "this is not the last page"}
        else:
            self.json_data = TEAMS_PAGE_TWO
            self.links = {}

        self.status_code = status_code

    def json(self):
        return json.loads(self.json_data)


def mock_list_org_teams(*args, **kwargs):
    if "FAILURE" in args[0]:
        return MockTeamList(404, 1)

    return MockTeamList(200, kwargs["params"]["page"])


class GitHubTeamWatcherTestCase(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        self.account_type = AccountType(name="GitHub")
        db.session.add(self.account_type)
        db.session.commit()

        app.config["GITHUB_CREDENTIALS"] = {
            "Org-one": "token-one",
            "FAILURE": "FAILURE"
        }

        db.session.add(Account(name="Org-one", account_type_id=self.account_type.id,
                               identifier="Org-one", active=True, third_party=False))
        self.technology = Technology(name="organization")
        db.session.add(self.technology)

        db.session.commit()

    @mock.patch("requests.get", side_effect=mock_list_org_teams)
    def test_list_org_teams(self, mock_get):
        from security_monkey.watchers.github.team import GitHubTeam
        team_watcher = GitHubTeam(accounts=["Org-one"])

        result = team_watcher.list_org_teams("Org-one")
        assert len(result) == 2
        assert result[0]["name"] == "Justice League"
        assert result[1]["name"] == "Team2"

        with self.assertRaises(InvalidResponseCodeFromGitHubError) as _:
            team_watcher.list_org_teams("FAILURE")

    @mock.patch("requests.get", side_effect=mock_list_org_teams)
    def test_slurp(self, mock_get):
        from security_monkey.watchers.github.team import GitHubTeam
        team_watcher = GitHubTeam(accounts=["Org-one"])

        result, exc = team_watcher.slurp()
        assert exc == {}
        assert len(result) == 2
        assert result[0].account == "Org-one"
        assert result[0].name == "Justice League"
        assert result[0].index == "team"
        assert len(ExceptionLogs.query.all()) == 0

        # And failures:
        db.session.add(Account(name="FAILURE", account_type_id=self.account_type.id,
                               identifier="FAILURE", active=True, third_party=False))
        db.session.commit()
        team_watcher = GitHubTeam(accounts=["FAILURE"])

        result, exc = team_watcher.slurp()
        assert len(exc) == 1
        assert len(ExceptionLogs.query.all()) == 1
