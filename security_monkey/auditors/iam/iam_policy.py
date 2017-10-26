#     Copyright 2014 Netflix, Inc.
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
.. module: security_monkey.auditors.iam.iam_policy
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.auditor import Auditor, Categories
from security_monkey.watchers.iam.managed_policy import ManagedPolicy
from security_monkey import app
import json


class IAMPolicyAuditor(Auditor):

    explicit_iam_checks = [
        "iam:*",
        "iam:passrole"
    ]

    def __init__(self, accounts=None, debug=False):
        super(IAMPolicyAuditor, self).__init__(accounts=accounts, debug=debug)
        self.iam_policy_keys = ['InlinePolicies']

    def load_policies(self, item):
        policies = list()
        for key in self.iam_policy_keys:
            try:
                policy = dpath.util.values(item.config, key, separator='$')
                if isinstance(policy, list):
                    for p in policy:
                        if not p:
                            continue
                        if isinstance(p, list):
                            policies.extend([Policy(pp) for pp in p])
                        else:
                            policies.append(Policy(p))
                else:
                    policies.append(Policy(policy))
            except PathNotFound:
                continue
        return policies

    def check_star_privileges(self, item):
        """
        alert when an IAM Object has a policy allowing '*'.
        """
        issue = Categories.ADMIN_ACCESS
        notes = Categories.ADMIN_ACCESS_NOTES

        for policy in self.load_policies(item):
            for statement in policy.statements:
                if statement.effect == "Allow":
                    if '*' in statement.actions:
                        resources = json.dumps(sorted(list(statement.resources)))
                        notes = notes.format(actions='["*"]', resource=resources)
                        self.add_issue(10, issue, item, notes=notes)

    def check_iam_star_privileges(self, item):
        """
        alert when an IAM Object has a policy allowing 'iam:*'.
        """
        issue = Categories.ADMIN_ACCESS
        notes = Categories.ADMIN_ACCESS_NOTES

        for policy in self.load_policies(item):
            for statement in policy.statements:
                if statement.effect == 'Allow':
                    actions = {action.lower() for action in statement.actions}
                    if 'iam:*' in actions:
                        resources = json.dumps(sorted(list(statement.resources)))
                        notes = notes.format(actions='["iam:*"]', resource=resources)
                        self.add_issue(10, issue, item, notes=notes)

    def check_iam_mutating_privileges(self, item):
        """
        alert when an IAM Object has a policy allowing mutating IAM permissions.
        """
        issue = Categories.SENSITIVE_PERMISSIONS
        notes = CATEGORIES.SENSITIVE_PERMISSIONS_NOTES

        mutating_iam_prefixes = [
            'add', 'attach', 'create', 'delete', 'detach', 'put', 'remove', 'set', 'update', 'upload'
        ]

        for policy in self.load_policies(item):
            for statement in policy.statements:
                mutating_actions = set()
                if statement.effect == 'Allow':
                    for action in statement.actions_expanded:
                        if not action.lower().startswith('iam:'):
                            continue

                        for prefix in mutating_iam_prefixes:
                            if action.lower().startswith(prefix):
                                mutating_actions.add(action)

                    if mutating_actions:
                        resources = json.dumps(sorted(list(statement.resources)))
                        actions = json.dumps(sorted(list(mutating_actions)))
                        notes = notes.format(actions=actions, resource=resources)
                        self.add_issue(10, issue, item, notes=notes)

    def check_iam_passrole(self, item):
        """
        alert when an IAM Object has a policy allowing 'iam:PassRole'.
        This allows the object to pass any role specified in the resource block to an ec2 instance.
        """
        issue = Categories.SENSITIVE_PERMISSIONS
        notes = CATEGORIES.SENSITIVE_PERMISSIONS_NOTES

        for policy in self.load_policies(item):
            for statement in policy.statements:
                if statement.effect == 'Allow':
                    if 'iam:passrole' in statement.actions_expanded:
                        resources = json.dumps(sorted(list(statement.resources)))
                        notes = notes.format(actions='["iam:passrole"]', resource=resources)
                        self.add_issue(10, issue, item, notes=notes)

    def check_notaction(self, item):
        """
        alert when an IAM Object has a policy containing 'NotAction'.
        NotAction combined with an "Effect": "Allow" often provides more privilege
        than is desired.
        """
        issue = Categories.STATEMENT_CONSTRUCTION
        notes = Categories.STATEMENT_CONSTRUCTION_NOTES

        for policy in self.load_policies(item):
            for statement in policy.statements:
                if statement.effect == 'Allow':
                    if 'NotAction' in statement.statement:
                        notes = notes.format(construct='["NotAction"]'
                        self.add_issue(10, issue, item, notes=notes)

    def check_notresource(self, item):
        """
        alert when an IAM Object has a policy containing 'NotResoure'.
        NotResource combined with an "Effect": "Allow" often provides more privilege
        than is desired.
        """
        issue = Categories.STATEMENT_CONSTRUCTION
        notes = Categories.STATEMENT_CONSTRUCTION_NOTES

        for policy in self.load_policies(item):
            for statement in policy.statements:
                if statement.effect == 'Allow':
                    if 'NotResource' in statement.statement:
                        notes = notes.format(construct='["NotResource"]'
                        self.add_issue(10, issue, item, notes=notes)

    def check_security_group_permissions(self, item):
        """
        alert when an IAM Object has ec2:AuthorizeSecurityGroupEgress or ec2:AuthorizeSecurityGroupIngress.
        """
        issue = Categories.SENSITIVE_PERMISSIONS
        notes = Categories.SENSITIVE_PERMISSIONS_NOTES

        permissions = {"ec2:authorizesecuritygroupegress", "ec2:authorizesecuritygroupingress"}

        for policy in self.load_policies(item):
            for statement in policy.statements:
                if statement.effect == 'Allow':
                    permissions = statement.actions_expanded.intersection(permissions)
                    if permissions:
                        resources = json.dumps(sorted(list(statement.resources)))
                        actions = json.dumps(sorted(list(permissions)))
                        notes = notes.format(actions=actions, resource=resources)
                        self.add_issue(7, issue, item, notes=notes)

    def library_check_attached_managed_policies(self, iam_item, iam_type):
        """
        alert when an IAM item (group, user or role) is attached to a managed policy with issues
        """
        mp_items = self.get_auditor_support_items(ManagedPolicy.index, iam_item.account)
        managed_policies = iam_item.config.get('managed_policies', iam_item.config.get('ManagedPolicies'))
        for item_mp in managed_policies or []:
            found = False
            item_mp_arn = item_mp.get('arn', item_mp.get('Arn'))
            for mp_item in mp_items or [] and not found:
                mp_arn = mp_item.config.get('arn', mp_item.config.get('Arn'))
                if mp_arn == item_mp_arn:
                    found = True
                    self.link_to_support_item_issues(iam_item, mp_item.db_item, None, "Found issue(s) in attached Managed Policy")

            if not found:
                app.logger.error("IAM Managed Policy defined but not found for {}-{}".format(iam_item.index, iam_item.name))
