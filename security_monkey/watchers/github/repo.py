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
    :synopsis: Watcher for GitHub Repositories (within an organization).


.. version:: $$VERSION$$
.. moduleauthor:: Mike Grima <mgrima@netflix.com>

"""
from security_monkey.common.github.util import get_github_creds, iter_org, strip_url_fields
from security_monkey.datastore import Account
from security_monkey.decorators import record_exception
from security_monkey.exceptions import InvalidResponseCodeFromGitHubError, InvalidResponseCodeFromGitHubRepoError
from security_monkey.watcher import Watcher, ChangeItem
import requests
from security_monkey import app

GITHUB_URL = "https://api.github.com/"


class GitHubRepo(Watcher):
    index = 'repository'
    i_am_singular = 'repository'
    i_am_plural = 'repositories'
    account_type = 'GitHub'

    def __init__(self, accounts=None, debug=False):
        super(GitHubRepo, self).__init__(accounts=accounts, debug=debug)
        self.honor_ephemerals = True
        self.ephemeral_paths = [
            "updated_at",
            "stargazers_count",
            "pushed_at",
            "size",
            "watchers",
            "watchers_count",
            "forks",
            "forks_count",
            "open_issues",
            "open_issues_count",
            "releases",
            "webhooks$*$last_response",
            "webhooks$*$updated_at"
        ]
        self.batched_size = 20
        self.done_slurping = False
        self.github_creds = get_github_creds(self.accounts)

    def slurp_list(self):
        app.logger.debug("Preparing for GitHub repository listing...")
        self.prep_for_batch_slurp()

        @record_exception(source="{index}-list-watcher".format(index=self.index))
        def fetch_repo_list(**kwargs):
            account = Account.query.filter(Account.name == kwargs["account_name"]).first()
            app.logger.debug("Fetching repo list for org: {}".format(account.identifier))

            repos = self.list_org_repos(account.identifier)
            return repos, kwargs["exception_map"]

        @iter_org(orgs=self.accounts)
        def list_all_repos(**kwargs):
            # Are we skipping this org?
            if self.check_ignore_list(kwargs["account_name"]):
                app.logger.debug("Skipping ignored account: {}".format(kwargs["account_name"]))
                return [], kwargs["exception_map"]

            # Exception handling complexities...
            results = fetch_repo_list(**kwargs)
            if not results:
                return [], kwargs["exception_map"]

            return results

        self.total_list, exc = list_all_repos(index=self.index)

        return self.total_list, exc

    def slurp(self):
        app.logger.debug("Now processing batch #{}".format(self.batch_counter + 1))
        exception_map = {}
        account_dict = {}
        for account in self.accounts:
            account_db = Account.query.filter(Account.name == account).first()
            account_dict[account_db.identifier] = account

        @record_exception(source="{index}-fetcher".format(index=self.index))
        def fetch_additional_repo_details(**kwargs):
            app.logger.debug("Fetching deploy keys for repo: {}/{}".format(kwargs["org"], kwargs["repo"]["name"]))
            kwargs["repo"]["deploy_keys"] = self.list_repo_deploy_keys(kwargs["org"], kwargs["repo"]["name"])

            app.logger.debug("Fetching outside collaborators for repo: {}/{}".format(kwargs["org"], kwargs["repo"]["name"]))
            kwargs["repo"]["outside_collaborators"] = self.list_repo_outside_collaborators(kwargs["org"], kwargs["repo"]["name"])

            app.logger.debug("Fetching protected branches for repo: {}/{}".format(kwargs["org"], kwargs["repo"]["name"]))
            kwargs["repo"]["protected_branches"] = self.list_repo_protected_branches(kwargs["org"], kwargs["repo"]["name"])

            app.logger.debug("Fetching releases for repo: {}/{}".format(kwargs["org"], kwargs["repo"]["name"]))
            kwargs["repo"]["releases"] = self.list_repo_releases(kwargs["org"], kwargs["repo"]["name"])

            app.logger.debug("Fetching webhooks for repo: {}/{}".format(kwargs["org"], kwargs["repo"]["name"]))
            kwargs["repo"]["webhooks"] = self.list_repo_webhooks(kwargs["org"], kwargs["repo"]["name"])

            app.logger.debug("Fetching team permissions for repo: {}/{}".format(kwargs["org"], kwargs["repo"]["name"]))
            kwargs["repo"]["team_permissions"] = self.list_repo_team_permissions(kwargs["org"], kwargs["repo"]["name"])

            return True

        @record_exception(source="{index}-watcher".format(index=self.index))
        def fetch_each_repo_details(**kwargs):
            item_list = []
            item_counter = self.batch_counter * self.batched_size

            while self.batched_size - len(item_list) > 0 and not self.done_slurping:
                cursor = self.total_list[item_counter]
                org_name = cursor["owner"]["login"]

                app.logger.debug("Fetching details for repo: {}/{}".format(org_name, cursor["name"]))
                additional_details = fetch_additional_repo_details(index=self.index,
                                                                   account_name=account_dict[org_name],
                                                                   name=cursor["name"],
                                                                   region="universal",
                                                                   org=org_name,
                                                                   repo=cursor)
                if additional_details:
                    cursor["Arn"] = cursor["full_name"]
                    cursor = strip_url_fields(cursor)
                    item = GitHubRepoItem(account=account_dict[org_name],
                                          name=cursor["name"],
                                          arn=cursor["full_name"],
                                          config=cursor,
                                          source_watcher=self)
                    item_list.append(item)

                item_counter += 1
                if item_counter == len(self.total_list):
                    self.done_slurping = True

            self.batch_counter += 1

            return item_list, kwargs["exception_map"]

        result = fetch_each_repo_details(index=self.index, exception_map=exception_map)
        if not result:
            return [], exception_map

        return result

    def list_org_repos(self, org, type="all"):
        headers = {
            'Authorization': 'token {}'.format(self.github_creds[org])
        }

        params = {
            "page": 1,
            "type": type
        }
        done = False

        repos = []

        while not done:
            url = "https://api.github.com/orgs/{}/repos".format(org)
            result = requests.get(url, headers=headers, params=params)

            if result.status_code != 200:
                raise InvalidResponseCodeFromGitHubError(org, result.status_code)

            if not result.links.get("last"):
                done = True
            else:
                params["page"] += 1

            result_json = result.json()
            repos += result_json

        return repos

    def list_repo_deploy_keys(self, org, repo):
        api_part = 'repos/{}/{}/keys'.format(org, repo)

        headers = {
            'Authorization': 'token {}'.format(self.github_creds[org])
        }

        params = {
            "page": 1
        }
        done = False

        keys = []
        url = "{}{}".format(GITHUB_URL, api_part)

        while not done:
            result = requests.get(url, headers=headers, params=params)

            if result.status_code != 200:
                raise InvalidResponseCodeFromGitHubRepoError(org, repo, result.status_code)

            if not result.links.get("last"):
                done = True
            else:
                params["page"] += 1

            result_json = result.json()
            keys += result_json

        return keys

    def list_repo_protected_branches(self, org, repo):
        api_part = 'repos/{}/{}/branches'.format(org, repo)

        headers = {
            'Authorization': 'token {}'.format(self.github_creds[org]),
            'Accept': 'application/vnd.github.loki-preview+json'
        }

        params = {
            "page": 1,
            "protected": "true"  # GitHub strangeness... Needs to be a string :/
        }
        done = False

        branches = []
        url = "{}{}".format(GITHUB_URL, api_part)

        while not done:
            result = requests.get(url, headers=headers, params=params)

            if result.status_code != 200:
                raise InvalidResponseCodeFromGitHubRepoError(org, repo, result.status_code)

            if not result.links.get("last"):
                done = True
            else:
                params["page"] += 1

            result_json = result.json()
            for b in result_json:

                # I don't care so much about the commit itself.
                del b["commit"]
                branches.append(b)

        return branches

    def list_repo_outside_collaborators(self, org, repo):
        api_part = 'repos/{}/{}/collaborators'.format(org, repo)

        headers = {
            'Authorization': 'token {}'.format(self.github_creds[org])
        }

        params = {
            "page": 1,
            "affiliation": "outside"
        }
        done = False

        collabs = []
        url = "{}{}".format(GITHUB_URL, api_part)

        while not done:
            result = requests.get(url, headers=headers, params=params)

            if result.status_code != 200:
                raise InvalidResponseCodeFromGitHubRepoError(org, repo, result.status_code)

            if not result.links.get("last"):
                done = True
            else:
                params["page"] += 1

            result_json = result.json()
            collabs += result_json

        return collabs

    def list_repo_releases(self, org, repo):
        api_part = 'repos/{}/{}/releases'.format(org, repo)

        headers = {
            'Authorization': 'token {}'.format(self.github_creds[org])
        }

        params = {
            "page": 1
        }
        done = False

        releases = []
        url = "{}{}".format(GITHUB_URL, api_part)

        while not done:
            result = requests.get(url, headers=headers, params=params)

            if result.status_code != 200:
                raise InvalidResponseCodeFromGitHubRepoError(org, repo, result.status_code)

            if not result.links.get("last"):
                done = True
            else:
                params["page"] += 1

            result_json = result.json()
            for r in result_json:
                # We only care about a few fields:
                release = {
                    "author": r["author"]["login"],
                    "created_at": r["created_at"],
                    "draft": r["draft"],
                    "id": r["id"],
                    "name": r["name"],
                    "prerelease": r["prerelease"],
                    "tag_name": r["tag_name"],
                    "target_commitish": r["target_commitish"],
                    "url": r["url"]
                }

                releases.append(release)

        return releases

    def list_repo_webhooks(self, org, repo):
        api_part = 'repos/{}/{}/hooks'.format(org, repo)

        headers = {
            'Authorization': 'token {}'.format(self.github_creds[org])
        }

        params = {
            "page": 1
        }
        done = False

        webhooks = []
        url = "{}{}".format(GITHUB_URL, api_part)

        while not done:
            result = requests.get(url, headers=headers, params=params)

            if result.status_code != 200:
                raise InvalidResponseCodeFromGitHubRepoError(org, repo, result.status_code)

            if not result.links.get("last"):
                done = True
            else:
                params["page"] += 1

            result_json = result.json()
            webhooks += result_json

        return webhooks

    def list_repo_team_permissions(self, org, repo):
        api_part = 'repos/{}/{}/teams'.format(org, repo)

        headers = {
            'Authorization': 'token {}'.format(self.github_creds[org])
        }

        params = {
            "page": 1
        }
        done = False

        teams = {}
        url = "{}{}".format(GITHUB_URL, api_part)

        while not done:
            result = requests.get(url, headers=headers, params=params)

            if result.status_code != 200:
                raise InvalidResponseCodeFromGitHubRepoError(org, repo, result.status_code)

            if not result.links.get("last"):
                done = True
            else:
                params["page"] += 1

            result_json = result.json()
            for r in result_json:
                teams[r["name"]] = r["permission"]

        return teams


class GitHubRepoItem(ChangeItem):
    def __init__(self, account=None, name=None, arn=None, config=None, source_watcher=None):
        super(GitHubRepoItem, self).__init__(index=GitHubRepo.index,
                                             region="universal",
                                             account=account,
                                             name=name,
                                             arn=arn,
                                             new_config=config if config else {},
                                             source_watcher=source_watcher)
