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
.. module: security_monkey.tests.utilities.test_github_utils
    :platform: Unix
.. version:: $$VERSION$$
.. moduleauthor::  Mike Grima <mgrima@netflix.com>
"""
import json

from security_monkey import db, app
from security_monkey.common.github.util import get_github_creds, iter_org, strip_url_fields
from security_monkey.datastore import AccountType, Account, AccountTypeCustomValues
from security_monkey.exceptions import GitHubCredsError
from security_monkey.tests import SecurityMonkeyTestCase


class GitHubUtilsTestCase(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        # Delete any remaining test cruft:
        if app.config.get("GITHUB_CREDENTIALS"):
            del app.config["GITHUB_CREDENTIALS"]

        self.account_type = AccountType(name="GitHub")
        self.accounts = []
        db.session.add(self.account_type)
        db.session.commit()

        # Tests need to be run from the working dir such that `security_monkey/tests/utilities/templates/github_creds`
        # can be found!
        for x in ["one", "two", "three"]:
            account = Account(name="Org-{}".format(x), account_type_id=self.account_type.id,
                                   identifier="Org-{}".format(x), active=True)
            account.custom_fields.append(AccountTypeCustomValues(name="access_token_file",
                                                                 value="security_monkey/tests/"
                                                                       "utilities/templates/github_creds"))
            db.session.add(account)
            self.accounts.append(account)

        db.session.commit()

    def test_get_creds_file(self):
        # Load the creds file:
        creds = get_github_creds(["Org-one", "Org-two", "Org-three"])

        for x in ["one", "two", "three"]:
            assert creds["Org-{}".format(x)] == "token-{}".format(x)

        # And without one specified:
        db.session.add(Account(name="Org-BAD", account_type_id=self.account_type.id,
                               identifier="Org-BAD", active=True))
        db.session.commit()

        with self.assertRaises(GitHubCredsError) as _:
            get_github_creds(["Org-BAD"])

    def test_get_creds_env(self):
        app.config["GITHUB_CREDENTIALS"] = {
            "AnotherOrg": "AnotherCred"
        }

        db.session.add(Account(name="AnotherOrg", account_type_id=self.account_type.id,
                               identifier="AnotherOrg", active=True))
        db.session.commit()

        creds = get_github_creds(["AnotherOrg"])
        assert isinstance(creds, dict)
        assert creds["AnotherOrg"] == "AnotherCred"

        # Altogether now:
        creds = get_github_creds(["Org-one", "Org-two", "Org-three", "AnotherOrg"])
        assert isinstance(creds, dict)
        assert len(list(creds.keys())) == 4

    def test_iter_org_decorator(self):
        org_list = ["Org-one", "Org-two", "Org-three"]

        @iter_org(orgs=["Org-one", "Org-two", "Org-three"])
        def some_func(**kwargs):
            assert kwargs["exception_map"] is not None
            assert kwargs["account_name"] in org_list
            org_list.remove(kwargs["account_name"])

            return [kwargs["account_name"]], kwargs["exception_map"]

        results = some_func()
        assert len(results[0]) == 3
        assert isinstance(results[1], dict)

    def test_strip_url_fields(self):
        # Public security monkey info:
        github_blob = json.loads("""
        {
            "id": 21290287,
            "name": "security_monkey",
            "full_name": "Netflix/security_monkey",
            "owner": {
                "login": "Netflix",
                "id": 913567,
                "avatar_url": "https://avatars3.githubusercontent.com/u/913567?v=4",
                "gravatar_id": "",
                "url": "https://api.github.com/users/Netflix",
                "html_url": "https://github.com/Netflix",
                "followers_url": "https://api.github.com/users/Netflix/followers",
                "following_url": "https://api.github.com/users/Netflix/following{/other_user}",
                "gists_url": "https://api.github.com/users/Netflix/gists{/gist_id}",
                "starred_url": "https://api.github.com/users/Netflix/starred{/owner}{/repo}",
                "subscriptions_url": "https://api.github.com/users/Netflix/subscriptions",
                "organizations_url": "https://api.github.com/users/Netflix/orgs",
                "repos_url": "https://api.github.com/users/Netflix/repos",
                "events_url": "https://api.github.com/users/Netflix/events{/privacy}",
                "received_events_url": "https://api.github.com/users/Netflix/received_events",
                "type": "Organization",
                "site_admin": false
            },
            "private": false,
            "html_url": "https://github.com/Netflix/security_monkey",
            "description": "Security Monkey",
            "fork": false,
            "url": "https://api.github.com/repos/Netflix/security_monkey",
            "forks_url": "https://api.github.com/repos/Netflix/security_monkey/forks",
            "keys_url": "https://api.github.com/repos/Netflix/security_monkey/keys{/key_id}",
            "collaborators_url": "https://api.github.com/repos/Netflix/security_monkey/collaborators{/collaborator}",
            "teams_url": "https://api.github.com/repos/Netflix/security_monkey/teams",
            "hooks_url": "https://api.github.com/repos/Netflix/security_monkey/hooks",
            "issue_events_url": "https://api.github.com/repos/Netflix/security_monkey/issues/events{/number}",
            "events_url": "https://api.github.com/repos/Netflix/security_monkey/events",
            "assignees_url": "https://api.github.com/repos/Netflix/security_monkey/assignees{/user}",
            "branches_url": "https://api.github.com/repos/Netflix/security_monkey/branches{/branch}",
            "tags_url": "https://api.github.com/repos/Netflix/security_monkey/tags",
            "blobs_url": "https://api.github.com/repos/Netflix/security_monkey/git/blobs{/sha}",
            "git_tags_url": "https://api.github.com/repos/Netflix/security_monkey/git/tags{/sha}",
            "git_refs_url": "https://api.github.com/repos/Netflix/security_monkey/git/refs{/sha}",
            "trees_url": "https://api.github.com/repos/Netflix/security_monkey/git/trees{/sha}",
            "statuses_url": "https://api.github.com/repos/Netflix/security_monkey/statuses/{sha}",
            "languages_url": "https://api.github.com/repos/Netflix/security_monkey/languages",
            "stargazers_url": "https://api.github.com/repos/Netflix/security_monkey/stargazers",
            "contributors_url": "https://api.github.com/repos/Netflix/security_monkey/contributors",
            "subscribers_url": "https://api.github.com/repos/Netflix/security_monkey/subscribers",
            "subscription_url": "https://api.github.com/repos/Netflix/security_monkey/subscription",
            "commits_url": "https://api.github.com/repos/Netflix/security_monkey/commits{/sha}",
            "git_commits_url": "https://api.github.com/repos/Netflix/security_monkey/git/commits{/sha}",
            "comments_url": "https://api.github.com/repos/Netflix/security_monkey/comments{/number}",
            "issue_comment_url": "https://api.github.com/repos/Netflix/security_monkey/issues/comments{/number}",
            "contents_url": "https://api.github.com/repos/Netflix/security_monkey/contents/{+path}",
            "compare_url": "https://api.github.com/repos/Netflix/security_monkey/compare/{base}...{head}",
            "merges_url": "https://api.github.com/repos/Netflix/security_monkey/merges",
            "archive_url": "https://api.github.com/repos/Netflix/security_monkey/{archive_format}{/ref}",
            "downloads_url": "https://api.github.com/repos/Netflix/security_monkey/downloads",
            "issues_url": "https://api.github.com/repos/Netflix/security_monkey/issues{/number}",
            "pulls_url": "https://api.github.com/repos/Netflix/security_monkey/pulls{/number}",
            "milestones_url": "https://api.github.com/repos/Netflix/security_monkey/milestones{/number}",
            "notifications_url": "https://api.github.com/repos/Netflix/security_monkey/notifications{?since,all,participating}",
            "labels_url": "https://api.github.com/repos/Netflix/security_monkey/labels{/name}",
            "releases_url": "https://api.github.com/repos/Netflix/security_monkey/releases{/id}",
            "deployments_url": "https://api.github.com/repos/Netflix/security_monkey/deployments",
            "created_at": "2014-06-27T21:49:56Z",
            "updated_at": "2017-08-18T07:27:14Z",
            "pushed_at": "2017-08-19T08:27:57Z",
            "git_url": "git://github.com/Netflix/security_monkey.git",
            "ssh_url": "git@github.com:Netflix/security_monkey.git",
            "clone_url": "https://github.com/Netflix/security_monkey.git",
            "svn_url": "https://github.com/Netflix/security_monkey",
            "homepage": null,
            "size": 12497,
            "stargazers_count": 1602,
            "watchers_count": 1602,
            "language": "Python",
            "has_issues": true,
            "has_projects": true,
            "has_downloads": true,
            "has_wiki": true,
            "has_pages": false,
            "forks_count": 320,
            "mirror_url": null,
            "open_issues_count": 54,
            "forks": 320,
            "open_issues": 54,
            "watchers": 1602,
            "default_branch": "develop",
            "organization": {
                "login": "Netflix",
                "id": 913567,
                "avatar_url": "https://avatars3.githubusercontent.com/u/913567?v=4",
                "gravatar_id": "",
                "url": "https://api.github.com/users/Netflix",
                "html_url": "https://github.com/Netflix",
                "followers_url": "https://api.github.com/users/Netflix/followers",
                "following_url": "https://api.github.com/users/Netflix/following{/other_user}",
                "gists_url": "https://api.github.com/users/Netflix/gists{/gist_id}",
                "starred_url": "https://api.github.com/users/Netflix/starred{/owner}{/repo}",
                "subscriptions_url": "https://api.github.com/users/Netflix/subscriptions",
                "organizations_url": "https://api.github.com/users/Netflix/orgs",
                "repos_url": "https://api.github.com/users/Netflix/repos",
                "events_url": "https://api.github.com/users/Netflix/events{/privacy}",
                "received_events_url": "https://api.github.com/users/Netflix/received_events",
                "type": "Organization",
                "site_admin": false
            },
            "network_count": 320,
            "subscribers_count": 403
        }
        """)

        # Grab a list of all _url fields:
        outer_fields_to_remove = []
        total_outer_fields = len(list(github_blob.keys()))

        org_fields_to_remove = []
        total_org_fields = len(list(github_blob["organization"].keys()))

        owner_fields_to_remove = []
        total_owner_fields = len(list(github_blob["owner"].keys()))

        for field in github_blob.keys():
            if "_url" in field:
                outer_fields_to_remove.append(field)

        for field in github_blob["organization"].keys():
            if "_url" in field:
                org_fields_to_remove.append(field)

        for field in github_blob["owner"].keys():
            if "_url" in field:
                owner_fields_to_remove.append(field)

        # Remove the fields:
        new_blob = strip_url_fields(github_blob)

        assert total_outer_fields - len(outer_fields_to_remove) == len(list(new_blob.keys()))
        assert total_org_fields - len(org_fields_to_remove) == len(list(new_blob["organization"].keys()))
        assert total_owner_fields - len(owner_fields_to_remove) == len(list(new_blob["owner"].keys()))

        # And just for sanity:
        for outer in outer_fields_to_remove:
            assert not new_blob.get(outer)
        for org in org_fields_to_remove:
            assert not new_blob["organization"].get(org)
        for owner in owner_fields_to_remove:
            assert not new_blob["owner"].get(owner)
