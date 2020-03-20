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
.. module: security_monkey.tests.auditors.github.test_repo_auditor
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Mike Grima <mgrima@netflix.com>

"""
from security_monkey.datastore import Account, AccountType, Technology
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey import db

from security_monkey.watchers.github.org import GitHubOrgItem
from security_monkey.auditors.github.repo import GitHubRepoAuditor

CONFIG_ONE = {
    "id": 1296269,
    "owner": {
        "login": "octocat",
        "id": 1,
        "avatar_url": "https://github.com/images/error/octocat_happy.gif",
        "gravatar_id": "",
        "url": "https://api.github.com/users/octocat",
        "html_url": "https://github.com/octocat",
        "followers_url": "https://api.github.com/users/octocat/followers",
        "following_url": "https://api.github.com/users/octocat/following{/other_user}",
        "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
        "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
        "organizations_url": "https://api.github.com/users/octocat/orgs",
        "repos_url": "https://api.github.com/users/octocat/repos",
        "events_url": "https://api.github.com/users/octocat/events{/privacy}",
        "received_events_url": "https://api.github.com/users/octocat/received_events",
        "type": "User",
        "site_admin": False
    },
    "name": "Hello-World",
    "full_name": "octocat/Hello-World",
    "description": "This your first repo!",
    "private": False,
    "fork": False,
    "url": "https://api.github.com/repos/octocat/Hello-World",
    "html_url": "https://github.com/octocat/Hello-World",
    "archive_url": "http://api.github.com/repos/octocat/Hello-World/{archive_format}{/ref}",
    "assignees_url": "http://api.github.com/repos/octocat/Hello-World/assignees{/user}",
    "blobs_url": "http://api.github.com/repos/octocat/Hello-World/git/blobs{/sha}",
    "branches_url": "http://api.github.com/repos/octocat/Hello-World/branches{/branch}",
    "clone_url": "https://github.com/octocat/Hello-World.git",
    "collaborators_url": "http://api.github.com/repos/octocat/Hello-World/collaborators{/collaborator}",
    "comments_url": "http://api.github.com/repos/octocat/Hello-World/comments{/number}",
    "commits_url": "http://api.github.com/repos/octocat/Hello-World/commits{/sha}",
    "compare_url": "http://api.github.com/repos/octocat/Hello-World/compare/{base}...{head}",
    "contents_url": "http://api.github.com/repos/octocat/Hello-World/contents/{+path}",
    "contributors_url": "http://api.github.com/repos/octocat/Hello-World/contributors",
    "deployments_url": "http://api.github.com/repos/octocat/Hello-World/deployments",
    "downloads_url": "http://api.github.com/repos/octocat/Hello-World/downloads",
    "events_url": "http://api.github.com/repos/octocat/Hello-World/events",
    "forks_url": "http://api.github.com/repos/octocat/Hello-World/forks",
    "git_commits_url": "http://api.github.com/repos/octocat/Hello-World/git/commits{/sha}",
    "git_refs_url": "http://api.github.com/repos/octocat/Hello-World/git/refs{/sha}",
    "git_tags_url": "http://api.github.com/repos/octocat/Hello-World/git/tags{/sha}",
    "git_url": "git:github.com/octocat/Hello-World.git",
    "hooks_url": "http://api.github.com/repos/octocat/Hello-World/hooks",
    "issue_comment_url": "http://api.github.com/repos/octocat/Hello-World/issues/comments{/number}",
    "issue_events_url": "http://api.github.com/repos/octocat/Hello-World/issues/events{/number}",
    "issues_url": "http://api.github.com/repos/octocat/Hello-World/issues{/number}",
    "keys_url": "http://api.github.com/repos/octocat/Hello-World/keys{/key_id}",
    "labels_url": "http://api.github.com/repos/octocat/Hello-World/labels{/name}",
    "languages_url": "http://api.github.com/repos/octocat/Hello-World/languages",
    "merges_url": "http://api.github.com/repos/octocat/Hello-World/merges",
    "milestones_url": "http://api.github.com/repos/octocat/Hello-World/milestones{/number}",
    "mirror_url": "git:git.example.com/octocat/Hello-World",
    "notifications_url": "http://api.github.com/repos/octocat/Hello-World/notifications{?since, all, participating}",
    "pulls_url": "http://api.github.com/repos/octocat/Hello-World/pulls{/number}",
    "releases_url": "http://api.github.com/repos/octocat/Hello-World/releases{/id}",
    "ssh_url": "git@github.com:octocat/Hello-World.git",
    "stargazers_url": "http://api.github.com/repos/octocat/Hello-World/stargazers",
    "statuses_url": "http://api.github.com/repos/octocat/Hello-World/statuses/{sha}",
    "subscribers_url": "http://api.github.com/repos/octocat/Hello-World/subscribers",
    "subscription_url": "http://api.github.com/repos/octocat/Hello-World/subscription",
    "svn_url": "https://svn.github.com/octocat/Hello-World",
    "tags_url": "http://api.github.com/repos/octocat/Hello-World/tags",
    "teams_url": "http://api.github.com/repos/octocat/Hello-World/teams",
    "trees_url": "http://api.github.com/repos/octocat/Hello-World/git/trees{/sha}",
    "homepage": "https://github.com",
    "language": None,
    "forks_count": 9,
    "stargazers_count": 80,
    "watchers_count": 80,
    "size": 108,
    "default_branch": "master",
    "open_issues_count": 0,
    "topics": [
        "octocat",
        "atom",
        "electron",
        "API"
    ],
    "has_issues": True,
    "has_wiki": True,
    "has_pages": False,
    "has_downloads": True,
    "pushed_at": "2011-01-26T19:06:43Z",
    "created_at": "2011-01-26T19:01:12Z",
    "updated_at": "2011-01-26T19:14:43Z",
    "permissions": {
        "admin": False,
        "push": False,
        "pull": True
    },
    "allow_rebase_merge": True,
    "allow_squash_merge": True,
    "allow_merge_commit": True,
    "subscribers_count": 42,
    "network_count": 0,
    "protected_branches": [],
    "deploy_keys": [],
    "outside_collaborators": [],
    "team_permissions": {
        "myteam": "push"
    }
}


CONFIG_TWO = {
    "id": 1296269,
    "owner": {
        "login": "octocat",
        "id": 1,
        "avatar_url": "https://github.com/images/error/octocat_happy.gif",
        "gravatar_id": "",
        "url": "https://api.github.com/users/octocat",
        "html_url": "https://github.com/octocat",
        "followers_url": "https://api.github.com/users/octocat/followers",
        "following_url": "https://api.github.com/users/octocat/following{/other_user}",
        "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
        "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
        "organizations_url": "https://api.github.com/users/octocat/orgs",
        "repos_url": "https://api.github.com/users/octocat/repos",
        "events_url": "https://api.github.com/users/octocat/events{/privacy}",
        "received_events_url": "https://api.github.com/users/octocat/received_events",
        "type": "User",
        "site_admin": False
    },
    "name": "Repo-Private",
    "full_name": "octocat/Repo-Private",
    "description": "This your second repo!",
    "private": True,
    "fork": True,
    "url": "https://api.github.com/repos/octocat/Hello-World",
    "html_url": "https://github.com/octocat/Hello-World",
    "archive_url": "http://api.github.com/repos/octocat/Hello-World/{archive_format}{/ref}",
    "assignees_url": "http://api.github.com/repos/octocat/Hello-World/assignees{/user}",
    "blobs_url": "http://api.github.com/repos/octocat/Hello-World/git/blobs{/sha}",
    "branches_url": "http://api.github.com/repos/octocat/Hello-World/branches{/branch}",
    "clone_url": "https://github.com/octocat/Hello-World.git",
    "collaborators_url": "http://api.github.com/repos/octocat/Hello-World/collaborators{/collaborator}",
    "comments_url": "http://api.github.com/repos/octocat/Hello-World/comments{/number}",
    "commits_url": "http://api.github.com/repos/octocat/Hello-World/commits{/sha}",
    "compare_url": "http://api.github.com/repos/octocat/Hello-World/compare/{base}...{head}",
    "contents_url": "http://api.github.com/repos/octocat/Hello-World/contents/{+path}",
    "contributors_url": "http://api.github.com/repos/octocat/Hello-World/contributors",
    "deployments_url": "http://api.github.com/repos/octocat/Hello-World/deployments",
    "downloads_url": "http://api.github.com/repos/octocat/Hello-World/downloads",
    "events_url": "http://api.github.com/repos/octocat/Hello-World/events",
    "forks_url": "http://api.github.com/repos/octocat/Hello-World/forks",
    "git_commits_url": "http://api.github.com/repos/octocat/Hello-World/git/commits{/sha}",
    "git_refs_url": "http://api.github.com/repos/octocat/Hello-World/git/refs{/sha}",
    "git_tags_url": "http://api.github.com/repos/octocat/Hello-World/git/tags{/sha}",
    "git_url": "git:github.com/octocat/Hello-World.git",
    "hooks_url": "http://api.github.com/repos/octocat/Hello-World/hooks",
    "issue_comment_url": "http://api.github.com/repos/octocat/Hello-World/issues/comments{/number}",
    "issue_events_url": "http://api.github.com/repos/octocat/Hello-World/issues/events{/number}",
    "issues_url": "http://api.github.com/repos/octocat/Hello-World/issues{/number}",
    "keys_url": "http://api.github.com/repos/octocat/Hello-World/keys{/key_id}",
    "labels_url": "http://api.github.com/repos/octocat/Hello-World/labels{/name}",
    "languages_url": "http://api.github.com/repos/octocat/Hello-World/languages",
    "merges_url": "http://api.github.com/repos/octocat/Hello-World/merges",
    "milestones_url": "http://api.github.com/repos/octocat/Hello-World/milestones{/number}",
    "mirror_url": "git:git.example.com/octocat/Hello-World",
    "notifications_url": "http://api.github.com/repos/octocat/Hello-World/notifications{?since, all, participating}",
    "pulls_url": "http://api.github.com/repos/octocat/Hello-World/pulls{/number}",
    "releases_url": "http://api.github.com/repos/octocat/Hello-World/releases{/id}",
    "ssh_url": "git@github.com:octocat/Hello-World.git",
    "stargazers_url": "http://api.github.com/repos/octocat/Hello-World/stargazers",
    "statuses_url": "http://api.github.com/repos/octocat/Hello-World/statuses/{sha}",
    "subscribers_url": "http://api.github.com/repos/octocat/Hello-World/subscribers",
    "subscription_url": "http://api.github.com/repos/octocat/Hello-World/subscription",
    "svn_url": "https://svn.github.com/octocat/Hello-World",
    "tags_url": "http://api.github.com/repos/octocat/Hello-World/tags",
    "teams_url": "http://api.github.com/repos/octocat/Hello-World/teams",
    "trees_url": "http://api.github.com/repos/octocat/Hello-World/git/trees{/sha}",
    "homepage": "https://github.com",
    "language": None,
    "forks_count": 9,
    "stargazers_count": 80,
    "watchers_count": 80,
    "size": 108,
    "default_branch": "master",
    "open_issues_count": 0,
    "topics": [
        "octocat",
        "atom",
        "electron",
        "API"
    ],
    "has_issues": True,
    "has_wiki": True,
    "has_pages": False,
    "has_downloads": True,
    "pushed_at": "2011-01-26T19:06:43Z",
    "created_at": "2011-01-26T19:01:12Z",
    "updated_at": "2011-01-26T19:14:43Z",
    "permissions": {
        "admin": False,
        "push": False,
        "pull": True
    },
    "allow_rebase_merge": True,
    "allow_squash_merge": True,
    "allow_merge_commit": True,
    "subscribers_count": 42,
    "network_count": 0,
    "protected_branches": [
        {
            "name": "master"
        }
    ],
    "deploy_keys": [
        {
            "id": 1234567890,
            "key": "ssh-rsa AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==",
            "url": "https://api.github.com/repos/octocat/Repo-Private/keys/1234567890",
            "title": "Some Deploy Key That Doesn't Exist",
            "verified": True,
            "created_at": "2017-02-01T00:56:06Z",
            "read_only": True
        },
        {
            "id": 1234567891,
            "key": "ssh-rsa AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==",
            "url": "https://api.github.com/repos/octocat/Repo-Private/keys/1234567891",
            "title": "Some OTHER Deploy Key That Doesn't Exist",
            "verified": True,
            "created_at": "2017-02-01T00:56:06Z",
            "read_only": False
        }
    ],
    "outside_collaborators": [
        {
            "login": "octocat",
            "id": 1,
            "avatar_url": "https://github.com/images/error/octocat_happy.gif",
            "gravatar_id": "",
            "url": "https://api.github.com/users/octocat",
            "html_url": "https://github.com/octocat",
            "followers_url": "https://api.github.com/users/octocat/followers",
            "following_url": "https://api.github.com/users/octocat/following{/other_user}",
            "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
            "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
            "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
            "organizations_url": "https://api.github.com/users/octocat/orgs",
            "repos_url": "https://api.github.com/users/octocat/repos",
            "events_url": "https://api.github.com/users/octocat/events{/privacy}",
            "received_events_url": "https://api.github.com/users/octocat/received_events",
            "type": "User",
            "site_admin": False,
            "permissions": {
                "pull": True,
                "push": True,
                "admin": False
            }
        },
        {
            "login": "octocat-admin",
            "id": 2,
            "avatar_url": "https://github.com/images/error/octocat_happy.gif",
            "gravatar_id": "",
            "url": "https://api.github.com/users/octocat-admin",
            "html_url": "https://github.com/octocat-admin",
            "followers_url": "https://api.github.com/users/octocat-admin/followers",
            "following_url": "https://api.github.com/users/octocat-admin/following{/other_user}",
            "gists_url": "https://api.github.com/users/octocat-admin/gists{/gist_id}",
            "starred_url": "https://api.github.com/users/octocat-admin/starred{/owner}{/repo}",
            "subscriptions_url": "https://api.github.com/users/octocat-admin/subscriptions",
            "organizations_url": "https://api.github.com/users/octocat-admin/orgs",
            "repos_url": "https://api.github.com/users/octocat-admin/repos",
            "events_url": "https://api.github.com/users/octocat-admin/events{/privacy}",
            "received_events_url": "https://api.github.com/users/octocat-admin/received_events",
            "type": "User",
            "site_admin": False,
            "permissions": {
                "pull": True,
                "push": True,
                "admin": True
            }
        }
    ],
    "team_permissions": {
        "myteam": "admin"
    }
}


class GitHubRepoAuditorTestCase(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        self.account_type = AccountType(name="GitHub")
        db.session.add(self.account_type)
        db.session.commit()

        db.session.add(Account(name="octocat", account_type_id=self.account_type.id,
                               identifier="octocat", active=True, third_party=False))
        self.technology = Technology(name="repository")
        db.session.add(self.technology)
        db.session.commit()

        self.gh_items = [
            GitHubOrgItem(account="octocat", name="Hello-World", arn="octocat/Hello-World", config=CONFIG_ONE),
            GitHubOrgItem(account="octocat", name="Repo-Private", arn="octocat/Repo-Private", config=CONFIG_TWO),
        ]

    def test_public_repo_check(self):
        repo_auditor = GitHubRepoAuditor(accounts=["octocat"])

        repo_auditor.check_for_public_repo(self.gh_items[0])
        repo_auditor.check_for_public_repo(self.gh_items[1])

        # Should raise issue:
        self.assertEqual(len(self.gh_items[0].audit_issues), 1)
        self.assertEqual(self.gh_items[0].audit_issues[0].score, 5)

        # Should not raise issues:
        self.assertEqual(len(self.gh_items[1].audit_issues), 0)

    def test_forked_repo_check(self):
        repo_auditor = GitHubRepoAuditor(accounts=["octocat"])

        repo_auditor.check_if_forked_repo(self.gh_items[0])
        repo_auditor.check_if_forked_repo(self.gh_items[1])

        # Should raise issue:
        self.assertEqual(len(self.gh_items[1].audit_issues), 1)
        self.assertEqual(self.gh_items[1].audit_issues[0].score, 3)

        # Should not raise issues:
        self.assertEqual(len(self.gh_items[0].audit_issues), 0)

    def test_no_protected_branches_check(self):
        repo_auditor = GitHubRepoAuditor(accounts=["octocat"])

        repo_auditor.check_for_no_protected_branches(self.gh_items[0])
        repo_auditor.check_for_no_protected_branches(self.gh_items[1])

        # Should raise issue:
        self.assertEqual(len(self.gh_items[0].audit_issues), 1)
        self.assertEqual(self.gh_items[0].audit_issues[0].score, 0)

        # Should not raise issues:
        self.assertEqual(len(self.gh_items[1].audit_issues), 0)

    def test_deploy_key_check(self):
        repo_auditor = GitHubRepoAuditor(accounts=["octocat"])

        repo_auditor.check_for_deploy_keys(self.gh_items[0])
        repo_auditor.check_for_deploy_keys(self.gh_items[1])

        # Should raise issue:
        self.assertEqual(len(self.gh_items[1].audit_issues), 2)
        self.assertEqual(self.gh_items[1].audit_issues[0].score, 3)
        self.assertEqual(self.gh_items[1].audit_issues[1].score, 5)

        # Should not raise issues:
        self.assertEqual(len(self.gh_items[0].audit_issues), 0)

    def test_outside_collaborators_check(self):
        repo_auditor = GitHubRepoAuditor(accounts=["octocat"])

        repo_auditor.check_for_outside_collaborators(self.gh_items[0])
        repo_auditor.check_for_outside_collaborators(self.gh_items[1])

        # Should raise issue:
        self.assertEqual(len(self.gh_items[1].audit_issues), 2)
        self.assertEqual(self.gh_items[1].audit_issues[0].score, 3)
        self.assertEqual(self.gh_items[1].audit_issues[1].score, 8)

        # Should not raise issues:
        self.assertEqual(len(self.gh_items[0].audit_issues), 0)

    def test_admin_teams_check(self):
        repo_auditor = GitHubRepoAuditor(accounts=["octocat"])

        repo_auditor.check_for_admin_teams(self.gh_items[0])
        repo_auditor.check_for_admin_teams(self.gh_items[1])

        # Should raise issue:
        self.assertEqual(len(self.gh_items[1].audit_issues), 1)
        self.assertEqual(self.gh_items[1].audit_issues[0].score, 3)

        # Should not raise issues:
        self.assertEqual(len(self.gh_items[0].audit_issues), 0)
