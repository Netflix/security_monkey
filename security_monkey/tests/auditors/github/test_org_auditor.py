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
.. module: security_monkey.tests.auditors.github.test_org_auditor
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Mike Grima <mgrima@netflix.com>

"""
from security_monkey.datastore import Account, AccountType, Technology
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey import db

from security_monkey.watchers.github.org import GitHubOrgItem
from security_monkey.auditors.github.org import GitHubOrgAuditor

CONFIG_ONE = {
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
    "company": None,
    "blog": "http://netflix.github.io/",
    "location": "Los Gatos, California",
    "email": "netflixoss@netflix.com",
    "has_organization_projects": None,
    "has_repository_projects": None,
    "public_repos": 130,
    "public_gists": 0,
    "followers": 0,
    "following": 0,
    "html_url": "https://github.com/Netflix",
    "created_at": "2011-07-13T20:20:01Z",
    "updated_at": "2017-08-16T09:44:42Z",
    "type": "Organization",
    "no_2fa_members": [],
    "owners": ["some-owner"]
}

CONFIG_TWO = {
    "login": "Netflix-PRIVATE",
    "id": 12345,
    "url": "https://api.github.com/orgs/Netflix-PRIVATE",
    "repos_url": "https://api.github.com/orgs/Netflix-PRIVATE/repos",
    "events_url": "https://api.github.com/orgs/Netflix-PRIVATE/events",
    "hooks_url": "https://api.github.com/orgs/Netflix-PRIVATE/hooks",
    "issues_url": "https://api.github.com/orgs/Netflix-PRIVATE/issues",
    "members_url": "https://api.github.com/orgs/Netflix-PRIVATE/members{/member}",
    "public_members_url": "https://api.github.com/orgs/Netflix-PRIVATE/public_members{/member}",
    "avatar_url": "https://avatars3.githubusercontent.com/u/12345?v=4",
    "description": "Netflix-PRIVATE",
    "name": "Netflix-PRIVATE.",
    "company": None,
    "blog": "",
    "location": "Los Gatos, California",
    "email": "",
    "has_organization_projects": None,
    "has_repository_projects": None,
    "public_repos": 0,
    "public_gists": 0,
    "followers": 0,
    "following": 0,
    "html_url": "https://github.com/Netflix-PRIVATE",
    "created_at": "2011-07-13T20:20:01Z",
    "updated_at": "2017-08-16T09:44:42Z",
    "type": "Organization",
    "no_2fa_members": [
        "user-one",
        "user-two"
    ],
    "owners": [
        "user-one"
    ]
}


class GitHubOrgAuditorTestCase(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        self.gh_items = [
            GitHubOrgItem(account="Netflix", name="Netflix", arn="Netflix", config=CONFIG_ONE),
            GitHubOrgItem(account="Netflix-PRIVATE", name="Netflix-PRIVATE", arn="Netflix-PRIVATE", config=CONFIG_TWO),
        ]

        self.account_type = AccountType(name="GitHub")
        db.session.add(self.account_type)
        db.session.commit()

        db.session.add(Account(name="Netflix", account_type_id=self.account_type.id,
                               identifier="Netflix", active=True, third_party=False))
        db.session.add(Account(name="Netflix-PRIVATE", account_type_id=self.account_type.id,
                               identifier="Netflix-PRIVATE", active=True, third_party=False))
        self.technology = Technology(name="organization")
        db.session.add(self.technology)
        db.session.commit()

    def test_public_repos_check(self):
        org_auditor = GitHubOrgAuditor(accounts=["Netflix", "Netflix-PRIVATE"])

        org_auditor.check_for_public_repo(self.gh_items[0])
        org_auditor.check_for_public_repo(self.gh_items[1])

        # Should raise issue:
        self.assertEqual(len(self.gh_items[0].audit_issues), 1)
        self.assertEqual(self.gh_items[0].audit_issues[0].score, 0)

        # Should not raise issues:
        self.assertEqual(len(self.gh_items[1].audit_issues), 0)

    def test_non_twofa_members_check(self):
        org_auditor = GitHubOrgAuditor(accounts=["Netflix", "Netflix-PRIVATE"])

        org_auditor.check_for_non_twofa_members(self.gh_items[0])
        org_auditor.check_for_non_twofa_members(self.gh_items[1])

        # Should raise issue:
        self.assertEqual(len(self.gh_items[0].audit_issues), 0)

        # Should not raise issues:
        self.assertEqual(len(self.gh_items[1].audit_issues), 2)
        self.assertEqual(self.gh_items[1].audit_issues[0].score, 2)
        self.assertEqual(self.gh_items[1].audit_issues[1].score, 10)
