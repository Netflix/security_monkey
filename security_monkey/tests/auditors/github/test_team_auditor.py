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
.. module: security_monkey.tests.auditors.github.test_team_auditor
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Mike Grima <mgrima@netflix.com>

"""
from security_monkey.datastore import Account, AccountType, Technology
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey import db

from security_monkey.watchers.github.team import GitHubTeamItem
from security_monkey.auditors.github.team import GitHubTeamAuditor

CONFIG_ONE = {
    "id": 1,
    "url": "https://api.github.com/teams/1",
    "name": "Justice League",
    "slug": "justice-league",
    "description": "A great team.",
    "privacy": "secret",
    "permission": "pull",
    "members_url": "https://api.github.com/teams/1/members{/member}",
    "repositories_url": "https://api.github.com/teams/1/repos"
}

CONFIG_TWO = {
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


class GitHubTeamAuditorTestCase(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        self.gh_items = [
            GitHubTeamItem(account="Org-one", name="Org-one", arn="Org-one", config=CONFIG_ONE),
            GitHubTeamItem(account="Org-one", name="Org-one", arn="Org-one", config=CONFIG_TWO),
        ]

        self.account_type = AccountType(name="GitHub")
        db.session.add(self.account_type)
        db.session.commit()

        db.session.add(Account(name="Org-one", account_type_id=self.account_type.id,
                               identifier="Org-one", active=True, third_party=False))
        self.technology = Technology(name="team")
        db.session.add(self.technology)
        db.session.commit()

    def test_public_team_check(self):
        team_auditor = GitHubTeamAuditor(accounts=["Org-one"])

        team_auditor.check_for_public_team(self.gh_items[0])
        team_auditor.check_for_public_team(self.gh_items[1])

        # Should raise issue:
        self.assertEqual(len(self.gh_items[1].audit_issues), 1)
        self.assertEqual(self.gh_items[1].audit_issues[0].score, 1)

        # Should not raise issues:
        self.assertEqual(len(self.gh_items[0].audit_issues), 0)
