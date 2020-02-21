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
.. module: security_monkey.tests.watchers.github.test_org
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

ORG_RESPONSE = """
{
    "login": "Netflix",
    "id": 913567,
    "url": "https://api.github.com/orgs/Netflix",
    "repos_url": "https://api.github.com/orgs/Netflix/repos",
    "events_url": "https://api.github.com/orgs/Netflix/events",
    "hooks_url": "https://api.github.com/orgs/Netflix/hooks",
    "issues_url": "https://api.github.com/orgs/Netflix/issues",
    "members_url": "https://api.github.com/orgs/Netflix/members{/member}",
    "public_members_url": "https://api.github.com/orgs/Netflix/public_members{/member}",
    "avatar_url": "https://avatars3.githubusercontent.com/u/913567?v=4",
    "description": "Netflix Open Source Platform",
    "name": "Netflix, Inc.",
    "company": null,
    "blog": "http://netflix.github.io/",
    "location": "Los Gatos, California",
    "email": "netflixoss@netflix.com",
    "has_organization_projects": true,
    "has_repository_projects": true,
    "public_repos": 130,
    "public_gists": 0,
    "followers": 0,
    "following": 0,
    "html_url": "https://github.com/Netflix",
    "created_at": "2011-07-13T20:20:01Z",
    "updated_at": "2017-08-16T09:44:42Z",
    "type": "Organization"
}"""

MEMBERS_PAGE_ONE = """[
    {
        "login": "----notarealuserone----",
        "id": 1,
        "avatar_url": "https://avatars0.githubusercontent.com/u/1?v=4",
        "gravatar_id": "",
        "url": "https://api.github.com/users/----notarealuserone----",
        "html_url": "https://github.com/----notarealuserone----",
        "followers_url": "https://api.github.com/users/----notarealuserone----/followers",
        "following_url": "https://api.github.com/users/----notarealuserone----/following{/other_user}",
        "gists_url": "https://api.github.com/users/----notarealuserone----/gists{/gist_id}",
        "starred_url": "https://api.github.com/users/----notarealuserone----/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/----notarealuserone----/subscriptions",
        "organizations_url": "https://api.github.com/users/----notarealuserone----/orgs",
        "repos_url": "https://api.github.com/users/----notarealuserone----/repos",
        "events_url": "https://api.github.com/users/----notarealuserone----/events{/privacy}",
        "received_events_url": "https://api.github.com/users/----notarealuserone----/received_events",
        "type": "User",
        "site_admin": false
    }
]"""

MEMBERS_PAGE_TWO = """
[
    {
        "login": "----notarealusertwo----",
        "id": 1728105,
        "avatar_url": "https://avatars1.githubusercontent.com/u/1728105?v=4",
        "gravatar_id": "",
        "url": "https://api.github.com/users/----notarealusertwo----",
        "html_url": "https://github.com/----notarealusertwo----",
        "followers_url": "https://api.github.com/users/----notarealusertwo----/followers",
        "following_url": "https://api.github.com/users/----notarealusertwo----/following{/other_user}",
        "gists_url": "https://api.github.com/users/----notarealusertwo----/gists{/gist_id}",
        "starred_url": "https://api.github.com/users/----notarealusertwo----/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/----notarealusertwo----/subscriptions",
        "organizations_url": "https://api.github.com/users/----notarealusertwo----/orgs",
        "repos_url": "https://api.github.com/users/----notarealusertwo----/repos",
        "events_url": "https://api.github.com/users/----notarealusertwo----/events{/privacy}",
        "received_events_url": "https://api.github.com/users/----notarealusertwo----/received_events",
        "type": "User",
        "site_admin": false
    }
]"""

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


class MockOrgDetails:
    def __init__(self, status_code):
        self.json_data = ORG_RESPONSE
        self.status_code = status_code

    def json(self):
        return json.loads(self.json_data)


def mock_get_org_details(*args, **kwargs):
    if args[0] == "https://api.github.com/orgs/FAILURE":
        return MockOrgDetails(404)

    return MockOrgDetails(200)


class MockMemberDetails:
    def __init__(self, status_code, page):
        if page == 1:
            self.json_data = MEMBERS_PAGE_ONE
            self.links = {"last": "this is not the last page"}
        else:
            self.json_data = MEMBERS_PAGE_TWO
            self.links = {}

        self.status_code = status_code

    def json(self):
        return json.loads(self.json_data)


def mock_get_member_details(*args, **kwargs):
    if "FAILURE" in args[0]:
        return MockMemberDetails(404, 1)

    return MockMemberDetails(200, kwargs["params"]["page"])


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


def mock_slurp(*args, **kwargs):
    if "members" in args[0] or "outside_collaborators" in args[0]:
        return mock_get_member_details(*args, **kwargs)

    elif "teams" in args[0]:
        return mock_list_org_teams(*args, **kwargs)

    return mock_get_org_details(*args, **kwargs)


class GitHubOrgWatcherTestCase(SecurityMonkeyTestCase):
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

    @mock.patch("requests.get", side_effect=mock_get_org_details)
    def test_get_org_details(self, mock_get):
        from security_monkey.watchers.github.org import GitHubOrg
        org_watcher = GitHubOrg(accounts=["Org-one"])

        result = org_watcher.get_org_details("Org-one")
        assert json.dumps(result, indent=4, sort_keys=True) == json.dumps(json.loads(ORG_RESPONSE), indent=4,
                                                                          sort_keys=True)

        with self.assertRaises(InvalidResponseCodeFromGitHubError) as _:
            org_watcher.get_org_details("FAILURE")

    @mock.patch("requests.get", side_effect=mock_get_member_details)
    def test_list_org_members(self, mock_get):
        from security_monkey.watchers.github.org import GitHubOrg
        org_watcher = GitHubOrg(accounts=["Org-one"])

        result = org_watcher.list_org_members("Org-one")
        assert len(result) == 2

        with self.assertRaises(InvalidResponseCodeFromGitHubError) as _:
            org_watcher.list_org_members("FAILURE")

    @mock.patch("requests.get", side_effect=mock_get_member_details)
    def test_list_org_outside_collabs(self, mock_get):
        from security_monkey.watchers.github.org import GitHubOrg
        org_watcher = GitHubOrg(accounts=["Org-one"])

        result = org_watcher.list_org_outside_collabs("Org-one")
        assert len(result) == 2

        with self.assertRaises(InvalidResponseCodeFromGitHubError) as _:
            org_watcher.list_org_outside_collabs("FAILURE")

    @mock.patch("requests.get", side_effect=mock_list_org_teams)
    def test_list_org_teams(self, mock_get):
        from security_monkey.watchers.github.org import GitHubOrg
        org_watcher = GitHubOrg(accounts=["Org-one"])

        result = org_watcher.list_org_teams("Org-one")
        assert len(result) == 2
        assert result[0] == "Justice League"
        assert result[1] == "Team2"

        with self.assertRaises(InvalidResponseCodeFromGitHubError) as _:
            org_watcher.list_org_teams("FAILURE")

    @mock.patch("requests.get", side_effect=mock_slurp)
    def test_slurp(self, mock_get):
        from security_monkey.watchers.github.org import GitHubOrg
        org_watcher = GitHubOrg(accounts=["Org-one"])

        result, exc = org_watcher.slurp()
        assert exc == {}
        assert len(result) == 1
        assert result[0].account == "Org-one"
        assert result[0].name == "Org-one"
        assert result[0].index == "organization"
        assert len(ExceptionLogs.query.all()) == 0

        # And failures:
        db.session.add(Account(name="FAILURE", account_type_id=self.account_type.id,
                               identifier="FAILURE", active=True, third_party=False))
        db.session.commit()
        org_watcher = GitHubOrg(accounts=["FAILURE"])

        result, exc = org_watcher.slurp()
        assert len(exc) == 1
        assert len(ExceptionLogs.query.all()) == 1
