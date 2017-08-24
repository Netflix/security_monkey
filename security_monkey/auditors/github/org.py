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
    :synopsis: Auditor for GitHub Organizations


.. version:: $$VERSION$$
.. moduleauthor:: Mike Grima <mgrima@netflix.com>

"""
from security_monkey.auditor import Auditor
from security_monkey.watchers.github.org import GitHubOrg


class GitHubOrgAuditor(Auditor):
    index = GitHubOrg.index
    i_am_singular = GitHubOrg.i_am_singular
    i_am_plural = GitHubOrg.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(GitHubOrgAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_for_public_repo(self, org_item):
        """
        Organizational view that it has public repositories. Default score of 0. This is mostly
        informational.
        :param org_item:
        :return:
        """
        tag = "Organization contains public repositories."

        if org_item.config["public_repos"] > 0:
            self.add_issue(0, tag, org_item, notes="Organization contains public repositories")

    def check_for_non_twofa_members(self, org_item):
        """
        Alert if the org has users that don't have 2FA enabled.

        Will keep this at a level of 2 -- unles there are admins without 2FA, then that is level 10!
        :param org_item:
        :return:
        """
        tag = "Organization contains users without 2FA enabled."
        owner_no_twofa = "Organization owner does NOT have 2FA enabled!"

        if len(org_item.config["no_2fa_members"]) > 0:
            self.add_issue(2, tag, org_item, notes="Organization contains users without 2FA enabled")

            for notwofa in org_item.config["no_2fa_members"]:
                if notwofa in org_item.config["owners"]:
                    self.add_issue(10, owner_no_twofa, org_item, notes="Organization OWNER: {} does NOT "
                                                                       "have 2FA enabled!".format(notwofa))
