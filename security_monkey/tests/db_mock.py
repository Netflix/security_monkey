#     Copyright 2016 Bridgewater Associates
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
.. module: security_monkey.tests.db_mock
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""


def parse_criteria(criteria):
    """
    Builds a unique key for the filter operator.
    Currently only supports column and value operations
    """
    left = criteria.left
    if left.__class__.__name__ == 'AnnotatedColumn':
        left_val = criteria.left.name
    else:
        # May add additional filter types as needed
        raise NotImplementedError()

    right = criteria.right
    if right.__class__.__name__ == 'BindParameter':
        right_val = criteria.right.value
    elif right.__class__.__name__ == 'False_':
        right_val = False
    elif right.__class__.__name__ == 'True_':
        right_val = True
    else:
        # May add additional filter types as needed
        raise NotImplementedError()

    return left_val, right_val


class MockAccountQuery():

    def __init__(self):
        self.test_accounts = []
        self.filtered_accounts = None

    def add_account(self, account):
        self.test_accounts.append(account)

    def clear(self):
        self.test_accounts = []

    def filter(self, *criterion):
        if self.filtered_accounts is None:
            self.filtered_accounts = list(self.test_accounts)

        matching_accounts = []

        for criteria in criterion:
            (left_val, right_val) = parse_criteria(criteria)
            for account in self.filtered_accounts:
                if getattr(account, left_val) == right_val:
                    matching_accounts.append(account)

        self.filtered_accounts = list(matching_accounts)
        return self

    def first(self):
        if self.filtered_accounts is not None:
            accounts = self.filtered_accounts
            self.filtered_accounts = None
        else:
            accounts = self.test_accounts

        if len(accounts) > 0:
            return accounts[0]
        return None

    def all(self):
        if self.filtered_accounts is not None:
            accounts = self.filtered_accounts
            self.filtered_accounts = None
        else:
            accounts = self.test_accounts

        return accounts


class MockDBSession():

    def expunge(self, item):
        pass

    def commit(self):
        pass
