# coding=utf-8
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
.. module: security_monkey.tests.watchers.github.test_repo
    :platform: Unix
.. version:: $$VERSION$$
.. moduleauthor::  Mike Grima <mgrima@netflix.com>
"""
import json

from security_monkey import app
from security_monkey.datastore import Account, Technology, AccountType, ExceptionLogs
from security_monkey.exceptions import InvalidResponseCodeFromGitHubError, InvalidResponseCodeFromGitHubRepoError
from security_monkey.tests import SecurityMonkeyTestCase, db

import mock

from security_monkey.watchers.github.repo import GitHubRepo

REPO_LIST_RESPONSE_PAGE_ONE = """
[
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
        "updated_at": "2017-08-20T09:53:11Z",
        "pushed_at": "2017-08-20T05:42:34Z",
        "git_url": "git://github.com/Netflix/security_monkey.git",
        "ssh_url": "git@github.com:Netflix/security_monkey.git",
        "clone_url": "https://github.com/Netflix/security_monkey.git",
        "svn_url": "https://github.com/Netflix/security_monkey",
        "homepage": null,
        "size": 12497,
        "stargazers_count": 1603,
        "watchers_count": 1603,
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
        "watchers": 1603,
        "default_branch": "develop",
        "permissions": {
            "admin": false,
            "push": false,
            "pull": true
        }
    }
]
"""

REPO_LIST_RESPONSE_PAGE_TWO = """
[
    {
        "id": 81116742,
        "name": "hubcommander",
        "full_name": "Netflix/hubcommander",
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
        "html_url": "https://github.com/Netflix/hubcommander",
        "description": "A Slack bot for GitHub organization management -- and other things too",
        "fork": false,
        "url": "https://api.github.com/repos/Netflix/hubcommander",
        "forks_url": "https://api.github.com/repos/Netflix/hubcommander/forks",
        "keys_url": "https://api.github.com/repos/Netflix/hubcommander/keys{/key_id}",
        "collaborators_url": "https://api.github.com/repos/Netflix/hubcommander/collaborators{/collaborator}",
        "teams_url": "https://api.github.com/repos/Netflix/hubcommander/teams",
        "hooks_url": "https://api.github.com/repos/Netflix/hubcommander/hooks",
        "issue_events_url": "https://api.github.com/repos/Netflix/hubcommander/issues/events{/number}",
        "events_url": "https://api.github.com/repos/Netflix/hubcommander/events",
        "assignees_url": "https://api.github.com/repos/Netflix/hubcommander/assignees{/user}",
        "branches_url": "https://api.github.com/repos/Netflix/hubcommander/branches{/branch}",
        "tags_url": "https://api.github.com/repos/Netflix/hubcommander/tags",
        "blobs_url": "https://api.github.com/repos/Netflix/hubcommander/git/blobs{/sha}",
        "git_tags_url": "https://api.github.com/repos/Netflix/hubcommander/git/tags{/sha}",
        "git_refs_url": "https://api.github.com/repos/Netflix/hubcommander/git/refs{/sha}",
        "trees_url": "https://api.github.com/repos/Netflix/hubcommander/git/trees{/sha}",
        "statuses_url": "https://api.github.com/repos/Netflix/hubcommander/statuses/{sha}",
        "languages_url": "https://api.github.com/repos/Netflix/hubcommander/languages",
        "stargazers_url": "https://api.github.com/repos/Netflix/hubcommander/stargazers",
        "contributors_url": "https://api.github.com/repos/Netflix/hubcommander/contributors",
        "subscribers_url": "https://api.github.com/repos/Netflix/hubcommander/subscribers",
        "subscription_url": "https://api.github.com/repos/Netflix/hubcommander/subscription",
        "commits_url": "https://api.github.com/repos/Netflix/hubcommander/commits{/sha}",
        "git_commits_url": "https://api.github.com/repos/Netflix/hubcommander/git/commits{/sha}",
        "comments_url": "https://api.github.com/repos/Netflix/hubcommander/comments{/number}",
        "issue_comment_url": "https://api.github.com/repos/Netflix/hubcommander/issues/comments{/number}",
        "contents_url": "https://api.github.com/repos/Netflix/hubcommander/contents/{+path}",
        "compare_url": "https://api.github.com/repos/Netflix/hubcommander/compare/{base}...{head}",
        "merges_url": "https://api.github.com/repos/Netflix/hubcommander/merges",
        "archive_url": "https://api.github.com/repos/Netflix/hubcommander/{archive_format}{/ref}",
        "downloads_url": "https://api.github.com/repos/Netflix/hubcommander/downloads",
        "issues_url": "https://api.github.com/repos/Netflix/hubcommander/issues{/number}",
        "pulls_url": "https://api.github.com/repos/Netflix/hubcommander/pulls{/number}",
        "milestones_url": "https://api.github.com/repos/Netflix/hubcommander/milestones{/number}",
        "notifications_url": "https://api.github.com/repos/Netflix/hubcommander/notifications{?since,all,participating}",
        "labels_url": "https://api.github.com/repos/Netflix/hubcommander/labels{/name}",
        "releases_url": "https://api.github.com/repos/Netflix/hubcommander/releases{/id}",
        "deployments_url": "https://api.github.com/repos/Netflix/hubcommander/deployments",
        "created_at": "2017-02-06T18:13:34Z",
        "updated_at": "2017-08-18T17:20:02Z",
        "pushed_at": "2017-07-24T21:12:23Z",
        "git_url": "git://github.com/Netflix/hubcommander.git",
        "ssh_url": "git@github.com:Netflix/hubcommander.git",
        "clone_url": "https://github.com/Netflix/hubcommander.git",
        "svn_url": "https://github.com/Netflix/hubcommander",
        "homepage": "",
        "size": 162,
        "stargazers_count": 623,
        "watchers_count": 623,
        "language": "Python",
        "has_issues": true,
        "has_projects": true,
        "has_downloads": true,
        "has_wiki": true,
        "has_pages": false,
        "forks_count": 71,
        "mirror_url": null,
        "open_issues_count": 4,
        "forks": 71,
        "open_issues": 4,
        "watchers": 623,
        "default_branch": "develop",
        "permissions": {
            "admin": false,
            "push": false,
            "pull": true
        }
    }
]"""

DEPLOY_KEY_RESPONSE_PAGE_ONE = """
[
    {
        "id": 1234567890,
        "key": "ssh-rsa AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==",
        "url": "https://api.github.com/repos/Netflix/security_monkey/keys/1234567890",
        "title": "Some Deploy Key That Doesn't Exist",
        "verified": true,
        "created_at": "2017-02-01T00:56:06Z",
        "read_only": true
    }
]"""

DEPLOY_KEY_RESPONSE_PAGE_TWO = """
[
    {
        "id": 1234567891,
        "key": "ssh-rsa AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==",
        "url": "https://api.github.com/repos/Netflix/security_monkey/keys/1234567891",
        "title": "Some OTHER Deploy Key That Doesn't Exist",
        "verified": true,
        "created_at": "2017-02-01T00:56:06Z",
        "read_only": true
    }
]"""

PROTECTED_BRANCHES_PAGE_ONE = """
[
    {
        "name": "master",
        "commit": {
            "sha": "fcfd1832eddf33859cbb49ffafbaeabf4466d1b6",
            "url": "https://api.github.com/repos/Netflix/security_monkey/commits/fcfd1832eddf33859cbb49ffafbaeabf4466d1b6"
        }
    }
]
"""

PROTECTED_BRANCHES_PAGE_TWO = """
[
    {
        "name": "develop",
        "commit": {
            "sha": "0f29754fcc300db912a263620fa4ef1f98241ee9",
            "url": "https://api.github.com/repos/Netflix/security_monkey/commits/0f29754fcc300db912a263620fa4ef1f98241ee9"
        }
    }
]
"""

OUTSIDE_COLLABORATOR_PAGE_ONE = """
[
    {
        "login": "----notarealuserone----",
        "id": 46346,
        "avatar_url": "https://avatars2.githubusercontent.com/u/46346?v=4",
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
        "site_admin": false,
        "permissions": {
            "admin": false,
            "push": false,
            "pull": true
        }
    }
]
"""

OUTSIDE_COLLABORATOR_PAGE_TWO = """
[
    {
        "login": "----notarealusertwo----",
        "id": 46346,
        "avatar_url": "https://avatars2.githubusercontent.com/u/46346?v=4",
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
        "site_admin": false,
        "permissions": {
            "admin": false,
            "push": false,
            "pull": true
        }
    }
]
"""

RELEASES_PAGE_ONE = """
[
    {
        "url": "https://api.github.com/repos/Netflix/security_monkey/releases/6140005",
        "assets_url": "https://api.github.com/repos/Netflix/security_monkey/releases/6140005/assets",
        "upload_url": "https://uploads.github.com/repos/Netflix/security_monkey/releases/6140005/assets{?name,label}",
        "html_url": "https://github.com/Netflix/security_monkey/releases/tag/v0.9.1",
        "id": 6140005,
        "tag_name": "v0.9.1",
        "target_commitish": "develop",
        "name": "Disjointed 🌿",
        "draft": false,
        "author": {
            "login": "monkeysecurity",
            "id": 8009126,
            "avatar_url": "https://avatars2.githubusercontent.com/u/8009126?v=4",
            "gravatar_id": "",
            "url": "https://api.github.com/users/monkeysecurity",
            "html_url": "https://github.com/monkeysecurity",
            "followers_url": "https://api.github.com/users/monkeysecurity/followers",
            "following_url": "https://api.github.com/users/monkeysecurity/following{/other_user}",
            "gists_url": "https://api.github.com/users/monkeysecurity/gists{/gist_id}",
            "starred_url": "https://api.github.com/users/monkeysecurity/starred{/owner}{/repo}",
            "subscriptions_url": "https://api.github.com/users/monkeysecurity/subscriptions",
            "organizations_url": "https://api.github.com/users/monkeysecurity/orgs",
            "repos_url": "https://api.github.com/users/monkeysecurity/repos",
            "events_url": "https://api.github.com/users/monkeysecurity/events{/privacy}",
            "received_events_url": "https://api.github.com/users/monkeysecurity/received_events",
            "type": "User",
            "site_admin": false
        },
        "prerelease": false,
        "created_at": "2017-04-20T18:42:26Z",
        "published_at": "2017-04-20T18:44:39Z",
        "assets": [
            {
                "url": "https://api.github.com/repos/Netflix/security_monkey/releases/assets/3702422",
                "id": 3702422,
                "name": "static.tar.gz",
                "label": null,
                "uploader": {
                    "login": "monkeysecurity",
                    "id": 8009126,
                    "avatar_url": "https://avatars2.githubusercontent.com/u/8009126?v=4",
                    "gravatar_id": "",
                    "url": "https://api.github.com/users/monkeysecurity",
                    "html_url": "https://github.com/monkeysecurity",
                    "followers_url": "https://api.github.com/users/monkeysecurity/followers",
                    "following_url": "https://api.github.com/users/monkeysecurity/following{/other_user}",
                    "gists_url": "https://api.github.com/users/monkeysecurity/gists{/gist_id}",
                    "starred_url": "https://api.github.com/users/monkeysecurity/starred{/owner}{/repo}",
                    "subscriptions_url": "https://api.github.com/users/monkeysecurity/subscriptions",
                    "organizations_url": "https://api.github.com/users/monkeysecurity/orgs",
                    "repos_url": "https://api.github.com/users/monkeysecurity/repos",
                    "events_url": "https://api.github.com/users/monkeysecurity/events{/privacy}",
                    "received_events_url": "https://api.github.com/users/monkeysecurity/received_events",
                    "type": "User",
                    "site_admin": false
                },
                "content_type": "application/x-gzip",
                "state": "uploaded",
                "size": 1168155,
                "download_count": 187,
                "created_at": "2017-04-20T18:44:30Z",
                "updated_at": "2017-04-20T18:44:31Z",
                "browser_download_url": "https://github.com/Netflix/security_monkey/releases/download/v0.9.1/static.tar.gz"
            }
        ],
        "tarball_url": "https://api.github.com/repos/Netflix/security_monkey/tarball/v0.9.1",
        "zipball_url": "https://api.github.com/repos/Netflix/security_monkey/zipball/v0.9.1",
        "body": "v0.9.1 ..."
    }
]
"""

RELEASES_PAGE_TWO = """
[
    {
        "url": "https://api.github.com/repos/Netflix/security_monkey/releases/6079555",
        "assets_url": "https://api.github.com/repos/Netflix/security_monkey/releases/6079555/assets",
        "upload_url": "https://uploads.github.com/repos/Netflix/security_monkey/releases/6079555/assets{?name,label}",
        "html_url": "https://github.com/Netflix/security_monkey/releases/tag/v0.9.0",
        "id": 6079555,
        "tag_name": "v0.9.0",
        "target_commitish": "develop",
        "name": "13 Reasons 📼🎧",
        "draft": false,
        "author": {
            "login": "monkeysecurity",
            "id": 8009126,
            "avatar_url": "https://avatars2.githubusercontent.com/u/8009126?v=4",
            "gravatar_id": "",
            "url": "https://api.github.com/users/monkeysecurity",
            "html_url": "https://github.com/monkeysecurity",
            "followers_url": "https://api.github.com/users/monkeysecurity/followers",
            "following_url": "https://api.github.com/users/monkeysecurity/following{/other_user}",
            "gists_url": "https://api.github.com/users/monkeysecurity/gists{/gist_id}",
            "starred_url": "https://api.github.com/users/monkeysecurity/starred{/owner}{/repo}",
            "subscriptions_url": "https://api.github.com/users/monkeysecurity/subscriptions",
            "organizations_url": "https://api.github.com/users/monkeysecurity/orgs",
            "repos_url": "https://api.github.com/users/monkeysecurity/repos",
            "events_url": "https://api.github.com/users/monkeysecurity/events{/privacy}",
            "received_events_url": "https://api.github.com/users/monkeysecurity/received_events",
            "type": "User",
            "site_admin": false
        },
        "prerelease": false,
        "created_at": "2017-04-14T02:20:36Z",
        "published_at": "2017-04-14T02:22:26Z",
        "assets": [
            {
                "url": "https://api.github.com/repos/Netflix/security_monkey/releases/assets/3651130",
                "id": 3651130,
                "name": "static.tar.gz",
                "label": null,
                "uploader": {
                    "login": "monkeysecurity",
                    "id": 8009126,
                    "avatar_url": "https://avatars2.githubusercontent.com/u/8009126?v=4",
                    "gravatar_id": "",
                    "url": "https://api.github.com/users/monkeysecurity",
                    "html_url": "https://github.com/monkeysecurity",
                    "followers_url": "https://api.github.com/users/monkeysecurity/followers",
                    "following_url": "https://api.github.com/users/monkeysecurity/following{/other_user}",
                    "gists_url": "https://api.github.com/users/monkeysecurity/gists{/gist_id}",
                    "starred_url": "https://api.github.com/users/monkeysecurity/starred{/owner}{/repo}",
                    "subscriptions_url": "https://api.github.com/users/monkeysecurity/subscriptions",
                    "organizations_url": "https://api.github.com/users/monkeysecurity/orgs",
                    "repos_url": "https://api.github.com/users/monkeysecurity/repos",
                    "events_url": "https://api.github.com/users/monkeysecurity/events{/privacy}",
                    "received_events_url": "https://api.github.com/users/monkeysecurity/received_events",
                    "type": "User",
                    "site_admin": false
                },
                "content_type": "application/x-gzip",
                "state": "uploaded",
                "size": 1168155,
                "download_count": 47,
                "created_at": "2017-04-14T02:30:33Z",
                "updated_at": "2017-04-14T02:30:34Z",
                "browser_download_url": "https://github.com/Netflix/security_monkey/releases/download/v0.9.0/static.tar.gz"
            }
        ],
        "tarball_url": "https://api.github.com/repos/Netflix/security_monkey/tarball/v0.9.0",
        "zipball_url": "https://api.github.com/repos/Netflix/security_monkey/zipball/v0.9.0",
        "body": "v0.9.0 ... "
    }
]
"""

WEBHOOK_PAGE_ONE = """
[
    {
        "type": "Repository",
        "id": 12345,
        "name": "EVENT-ONE",
        "active": true,
        "events": [
            "push"
        ],
        "config": {},
        "updated_at": "2016-03-25T17:31:28Z",
        "created_at": "2014-06-30T16:02:47Z",
        "url": "https://api.github.com/repos/Netflix/security_monkey/hooks/12345",
        "test_url": "https://api.github.com/repos/Netflix/security_monkey/hooks/12345/test",
        "ping_url": "https://api.github.com/repos/Netflix/security_monkey/hooks/12345/pings",
        "last_response": {
            "code": 200,
            "status": "active",
            "message": "OK"
        }
    }
]"""

WEBHOOK_PAGE_TWO = """
[
    {
        "type": "Repository",
        "id": 123456,
        "name": "EVENT-TWO",
        "active": true,
        "events": [
            "*"
        ],
        "config": {},
        "updated_at": "2016-03-28T18:24:57Z",
        "created_at": "2015-09-29T20:07:45Z",
        "url": "https://api.github.com/repos/Netflix/security_monkey/hooks/123456",
        "test_url": "https://api.github.com/repos/Netflix/security_monkey/hooks/123456/test",
        "ping_url": "https://api.github.com/repos/Netflix/security_monkey/hooks/123456/pings",
        "last_response": {
            "code": 200,
            "status": "active",
            "message": "OK"
        }
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
        "permission": "pull",
        "members_url": "https://api.github.com/teams/2/members{/member}",
        "repositories_url": "https://api.github.com/teams/2/repos"
    }
]"""


class MockRepoList:
    def __init__(self, status_code, page):
        if page == 1:
            self.json_data = REPO_LIST_RESPONSE_PAGE_ONE
            self.links = {"last": "this is not the last page"}
        else:
            self.json_data = REPO_LIST_RESPONSE_PAGE_TWO
            self.links = {}

        self.status_code = status_code

    def json(self):
        return json.loads(self.json_data)


def mock_list_repos(*args, **kwargs):
    if "FAILURE" in args[0]:
        return MockRepoList(404, 1)

    return MockRepoList(200, kwargs["params"]["page"])


class MockRepoKeyList:
    def __init__(self, status_code, page):
        if page == 1:
            self.json_data = DEPLOY_KEY_RESPONSE_PAGE_ONE
            self.links = {"last": "this is not the last page"}
        else:
            self.json_data = DEPLOY_KEY_RESPONSE_PAGE_TWO
            self.links = {}

        self.status_code = status_code

    def json(self):
        return json.loads(self.json_data)


def mock_list_repo_deploy_keys(*args, **kwargs):
    if "FAILURE" in args[0]:
        return MockRepoKeyList(404, 1)

    return MockRepoKeyList(200, kwargs["params"]["page"])


class MockRepoProtectedBranchesList:
    def __init__(self, status_code, page):
        if page == 1:
            self.json_data = PROTECTED_BRANCHES_PAGE_ONE
            self.links = {"last": "this is not the last page"}
        else:
            self.json_data = PROTECTED_BRANCHES_PAGE_TWO
            self.links = {}

        self.status_code = status_code

    def json(self):
        return json.loads(self.json_data)


def mock_list_repo_protected_branches(*args, **kwargs):
    if "FAILURE" in args[0]:
        return MockRepoProtectedBranchesList(404, 1)

    return MockRepoProtectedBranchesList(200, kwargs["params"]["page"])


class MockRepoOutsideCollaboratorsList:
    def __init__(self, status_code, page):
        if page == 1:
            self.json_data = OUTSIDE_COLLABORATOR_PAGE_ONE
            self.links = {"last": "this is not the last page"}
        else:
            self.json_data = OUTSIDE_COLLABORATOR_PAGE_TWO
            self.links = {}

        self.status_code = status_code

    def json(self):
        return json.loads(self.json_data)


def mock_list_repo_outside_collaborators(*args, **kwargs):
    if "FAILURE" in args[0]:
        return MockRepoOutsideCollaboratorsList(404, 1)

    return MockRepoOutsideCollaboratorsList(200, kwargs["params"]["page"])


class MockRepoReleasesList:
    def __init__(self, status_code, page):
        if page == 1:
            self.json_data = RELEASES_PAGE_ONE
            self.links = {"last": "this is not the last page"}
        else:
            self.json_data = RELEASES_PAGE_TWO
            self.links = {}

        self.status_code = status_code

    def json(self):
        return json.loads(self.json_data)


def mock_list_repo_releases(*args, **kwargs):
    if "FAILURE" in args[0]:
        return MockRepoReleasesList(404, 1)

    return MockRepoReleasesList(200, kwargs["params"]["page"])


class MockRepoWebhooksList:
    def __init__(self, status_code, page):
        if page == 1:
            self.json_data = WEBHOOK_PAGE_ONE
            self.links = {"last": "this is not the last page"}
        else:
            self.json_data = WEBHOOK_PAGE_TWO
            self.links = {}

        self.status_code = status_code

    def json(self):
        return json.loads(self.json_data)


def mock_list_repo_webhooks(*args, **kwargs):
    if "FAILURE" in args[0]:
        return MockRepoWebhooksList(404, 1)

    return MockRepoWebhooksList(200, kwargs["params"]["page"])


class MockRepoTeamsList:
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


def mock_list_repo_team_permissions(*args, **kwargs):
    if "FAILURE" in args[0]:
        return MockRepoTeamsList(404, 1)

    return MockRepoTeamsList(200, kwargs["params"]["page"])


def mock_slurp(*args, **kwargs):
    if "orgs" in args[0]:
        return mock_list_repos(*args, **kwargs)

    elif "keys" in args[0]:
        return mock_list_repo_deploy_keys(*args, **kwargs)

    elif "branches" in args[0]:
        return mock_list_repo_protected_branches(*args, **kwargs)

    elif "collaborators" in args[0]:
        return mock_list_repo_outside_collaborators(*args, **kwargs)

    elif "releases" in args[0]:
        return mock_list_repo_releases(*args, **kwargs)

    elif "teams" in args[0]:
        return mock_list_repo_team_permissions(*args, **kwargs)

    return mock_list_repo_webhooks(*args, **kwargs)


class GitHubRepoWatcherTestCase(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        self.account_type = AccountType(name="GitHub")
        db.session.add(self.account_type)
        db.session.commit()

        app.config["GITHUB_CREDENTIALS"] = {
            "Org-one": "token-one",
            "FAILURE": "FAILURE",
            "Netflix": "token-two"
        }

        db.session.add(Account(name="Org-one", account_type_id=self.account_type.id,
                               identifier="Org-one", active=True, third_party=False))
        self.technology = Technology(name="repository")
        db.session.add(self.technology)

        db.session.commit()

    @mock.patch("requests.get", side_effect=mock_list_repos)
    def test_list_repos(self, mock_get):
        from security_monkey.watchers.github.repo import GitHubRepo
        repo_watcher = GitHubRepo(accounts=["Org-one"])

        result = repo_watcher.list_org_repos("Org-one")
        assert len(result) == 2
        assert result[0]["name"] == "security_monkey"
        assert result[1]["name"] == "hubcommander"

        with self.assertRaises(InvalidResponseCodeFromGitHubError) as _:
            repo_watcher.list_org_repos("FAILURE")

    @mock.patch("requests.get", side_effect=mock_list_repo_deploy_keys)
    def test_list_repo_deploy_keys(self, mock_get):
        from security_monkey.watchers.github.repo import GitHubRepo
        repo_watcher = GitHubRepo(accounts=["Org-one"])

        result = repo_watcher.list_repo_deploy_keys("Org-one", "security_monkey")
        assert len(result) == 2
        assert result[0]["title"] == "Some Deploy Key That Doesn't Exist"
        assert result[1]["title"] == "Some OTHER Deploy Key That Doesn't Exist"

        with self.assertRaises(InvalidResponseCodeFromGitHubRepoError) as _:
            repo_watcher.list_repo_deploy_keys("FAILURE", "security_monkey")

    @mock.patch("requests.get", side_effect=mock_list_repo_protected_branches)
    def test_list_repo_protected_branches(self, mock_get):
        from security_monkey.watchers.github.repo import GitHubRepo
        repo_watcher = GitHubRepo(accounts=["Org-one"])

        result = repo_watcher.list_repo_protected_branches("Org-one", "security_monkey")
        assert len(result) == 2
        assert result[0]["name"] == "master"
        assert result[1]["name"] == "develop"

        with self.assertRaises(InvalidResponseCodeFromGitHubRepoError) as _:
            repo_watcher.list_repo_protected_branches("FAILURE", "security_monkey")

    @mock.patch("requests.get", side_effect=mock_list_repo_outside_collaborators)
    def test_list_repo_outside_collaborators(self, mock_get):
        from security_monkey.watchers.github.repo import GitHubRepo
        repo_watcher = GitHubRepo(accounts=["Org-one"])

        result = repo_watcher.list_repo_outside_collaborators("Org-one", "security_monkey")
        assert len(result) == 2
        assert result[0]["login"] == "----notarealuserone----"
        assert result[1]["login"] == "----notarealusertwo----"

        with self.assertRaises(InvalidResponseCodeFromGitHubRepoError) as _:
            repo_watcher.list_repo_outside_collaborators("FAILURE", "security_monkey")

    @mock.patch("requests.get", side_effect=mock_list_repo_releases)
    def test_list_repo_releases(self, mock_get):
        from security_monkey.watchers.github.repo import GitHubRepo
        repo_watcher = GitHubRepo(accounts=["Org-one"])

        result = repo_watcher.list_repo_releases("Org-one", "security_monkey")
        assert len(result) == 2
        assert result[0]["tag_name"] == "v0.9.1"
        assert result[1]["tag_name"] == "v0.9.0"

        with self.assertRaises(InvalidResponseCodeFromGitHubRepoError) as _:
            repo_watcher.list_repo_releases("FAILURE", "security_monkey")

    @mock.patch("requests.get", side_effect=mock_list_repo_webhooks)
    def test_list_repo_webhooks(self, mock_get):
        from security_monkey.watchers.github.repo import GitHubRepo
        repo_watcher = GitHubRepo(accounts=["Org-one"])

        result = repo_watcher.list_repo_webhooks("Org-one", "security_monkey")
        assert len(result) == 2
        assert result[0]["name"] == "EVENT-ONE"
        assert result[1]["name"] == "EVENT-TWO"

        with self.assertRaises(InvalidResponseCodeFromGitHubRepoError) as _:
            repo_watcher.list_repo_webhooks("FAILURE", "security_monkey")

    @mock.patch("requests.get", side_effect=mock_list_repo_team_permissions)
    def test_list_repo_team_permissions(self, mock_get):
        from security_monkey.watchers.github.repo import GitHubRepo
        repo_watcher = GitHubRepo(accounts=["Org-one"])

        result = repo_watcher.list_repo_team_permissions("Org-one", "security_monkey")
        assert len(result) == 2
        assert result["Justice League"] == "admin"
        assert result["Team2"] == "pull"

        with self.assertRaises(InvalidResponseCodeFromGitHubRepoError) as _:
            repo_watcher.list_repo_team_permissions("FAILURE", "security_monkey")

    @mock.patch("requests.get", side_effect=mock_list_repos)
    def test_slurp_list(self, mock_get):
        repo_watcher = GitHubRepo(accounts=["Org-one"])

        result, exc = repo_watcher.slurp_list()
        assert exc == {}
        assert len(result) == len(repo_watcher.total_list) == 2
        assert result[0]["name"] == "security_monkey"
        assert result[1]["name"] == "hubcommander"
        assert len(ExceptionLogs.query.all()) == 0

        # And failures:
        db.session.add(Account(name="FAILURE", account_type_id=self.account_type.id,
                               identifier="FAILURE", active=True, third_party=False))
        db.session.commit()
        repo_watcher = GitHubRepo(accounts=["FAILURE"])

        result, exc = repo_watcher.slurp()
        assert len(exc) == 1
        assert len(ExceptionLogs.query.all()) == 1

    @mock.patch("requests.get", side_effect=mock_slurp)
    def test_slurp(self, mock_get):
        db.session.add(Account(name="Netflix", account_type_id=self.account_type.id,
                               identifier="Netflix", active=True, third_party=False))
        db.session.commit()
        repo_watcher = GitHubRepo(accounts=["Netflix"])

        repo_watcher.slurp_list()
        result, exc = repo_watcher.slurp()

        assert len(result) == 2
        assert result[0].account == "Netflix"
        assert result[0].arn == "Netflix/security_monkey"
        assert result[0].index == "repository"
        assert len(exc) == 0
        assert len(ExceptionLogs.query.all()) == 0

        # Failures are a PITA to test here, so I'm just going to assume they work properly.
