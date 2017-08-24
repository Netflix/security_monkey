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
    :synopsis: Auditor for GitHub Organization Teams


.. version:: $$VERSION$$
.. moduleauthor:: Mike Grima <mgrima@netflix.com>

"""
from security_monkey.auditor import Auditor
from security_monkey.watchers.github.team import GitHubTeam


class GitHubTeamAuditor(Auditor):
    index = GitHubTeam.index
    i_am_singular = GitHubTeam.i_am_singular
    i_am_plural = GitHubTeam.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(GitHubTeamAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_for_public_team(self, team_item):
        """
        Teams that have the privacy flag set to "closed" are publicly visible.
        :param team_item:
        :return:
        """
        tag = "This team is no secret... to people in the org."

        if team_item.config["privacy"] == "closed":
            self.add_issue(1, tag, team_item, notes="Team is visible to all org members")
