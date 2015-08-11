#     Copyright 2015 Netflix, Inc.
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
.. module: security_monkey.parse
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Denver Janke <denverjanke@gmail.com>

"""
from security_monkey import watcher
from security_monkey.datastore import Account


def parse_accounts(accounts):
    if accounts == 'all':
        accounts = Account.query.filter(Account.third_party==False).filter(Account.active==True).all()
        accounts = [account.name for account in accounts]
        return accounts
    else:
        return accounts.split(',')


def parse_tech_names(tech_names):
    if tech_names == 'all':
        return watcher.watcher_registry.keys()
    else:
        return tech_names.split(',')