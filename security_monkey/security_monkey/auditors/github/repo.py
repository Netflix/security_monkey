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
.. module: security_monkey.watchers.github.repo
    :platform: Unix
    :synopsis: Auditor for GitHub Repositories (within an organization).


.. version:: $$VERSION$$
.. moduleauthor:: Mike Grima <mgrima@netflix.com>

"""
from six import itervalues

from security_monkey.auditor import Auditor
from security_monkey.watchers.github.repo import GitHubRepo


class GitHubRepoAuditor(Auditor):
    index = GitHubRepo.index
    i_am_singular = GitHubRepo.i_am_singular
    i_am_plural = GitHubRepo.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(GitHubRepoAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_for_public_repo(self, repo_item):
        """
        Alert when a repo is public. This may be benign, so we will assign by default, a score of 5.
        :param repo_item:
        :return:
        """
        tag = "Repo is public."

        if repo_item.config.get("private") is not None:
            if not repo_item.config["private"]:
                self.add_issue(5, tag, repo_item, notes="Public Repository")

    def check_if_forked_repo(self, repo_item):
        """
        Alert if a repo is a fork. Default score of 3
        :param repo_item:
        :return:
        """
        # GitHub doesn't provide a simple way to get the source of the fork for some reason... :/
        tag = "Repo is a fork of another repo."

        if repo_item.config.get("fork"):
            self.add_issue(3, tag, repo_item, notes="Repo is a fork of another repo")

    def check_for_no_protected_branches(self, repo_item):
        """
        Alert when a repo has 0 protected branches. This may be worth having for informational purposes.
        :param repo_item:
        :return:
        """
        tag = "Repo has no protected branches."

        if len(repo_item.config["protected_branches"]) == 0:
            self.add_issue(0, tag, repo_item, notes="No Protected Branches")

    def check_for_deploy_keys(self, repo_item):
        """
        Alert when a repo has deploy keys set. This may be benign, so we will assign by default, a score of 3.
        :param repo_item:
        :return:
        """
        tag = "Repo has deploy keys."
        push_tag = "Deploy key has PUSH access to the repo"

        if len(repo_item.config["deploy_keys"]) > 0:
            self.add_issue(3, tag, repo_item, notes="Repo has deploy keys")

            for key in repo_item.config["deploy_keys"]:
                if not key["read_only"]:
                    self.add_issue(5, push_tag, repo_item,
                                   notes="Key: {} can modify the repo".format(key["title"]))

    def check_for_outside_collaborators(self, repo_item):
        """
        Alert when repo has outside collaborators, as well as outside collaborators having admin access.
        :param repo_item:
        :return:
        """
        oc_tag = "Repo has outside collaborators."
        admin_oc_tag = "Repo has administrative outside collaborators."

        if len(repo_item.config["outside_collaborators"]) > 0:
            self.add_issue(3, oc_tag, repo_item, notes="Repo has outside collaborators")

            # Check if any of these OC's have administrative privileges:
            for oc in repo_item.config["outside_collaborators"]:
                if oc["permissions"]["admin"]:
                    self.add_issue(8, admin_oc_tag, repo_item,
                                   notes="{} has admin access to this repo.".format(oc["login"]))

    def check_for_admin_teams(self, repo_item):
        """
        Alert when repo has a team with admin permissions attached. Score = 3
        :param repo_item:
        :return:
        """
        tag = "Repo has teams with admin permissions."

        for permission in itervalues(repo_item.config["team_permissions"]):
            if permission == "admin":
                self.add_issue(3, tag, repo_item, notes="Repo has a team with admin permissions to it.")
