#     Copyright 2018 Netflix, Inc.
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
.. module: security_monkey.tests.apis.test_account
    :platform: Unix
.. version:: $$VERSION$$
.. moduleauthor::  Mike Grima <mgrima@netflix.com>
"""


def make_auth_header(token):
    return {
        'Authorization': 'Bearer {}'.format(token),
        'Content-Type': 'application/json'
    }


def test_fixtures(test_aws_accounts):
    from security_monkey.datastore import Account

    accounts = Account.query.all()
    assert len(accounts) == 5

    for a in accounts:
        assert a.type.name == "AWS"


def test_get_all_accounts(client, user_tokens, test_aws_accounts):
    from security_monkey.views.account import AccountPostList, api

    # No Auth:
    assert client.get(api.url_for(AccountPostList)).status_code == 401

    # With all users:
    for t in user_tokens.values():
        result = client.get(api.url_for(AccountPostList), headers=make_auth_header(t))
        assert result.status_code == 200

        assert len(result.json['items']) == len(test_aws_accounts) == result.json['total'] \
            == result.json['count']

    # 3rd party only:
    result = client.get(api.url_for(AccountPostList, third_party=True), headers=make_auth_header(t))
    assert result.status_code == 200
    assert len(result.json['items']) == result.json['count'] == result.json['total'] == 2

    # Inactive but first party:
    # TODO fix the filters for active and third party so they actually work
    result = client.get(api.url_for(AccountPostList, active=False, third_party=False), headers=make_auth_header(t))
    assert result.status_code == 200
    assert len(result.json['items']) == result.json['count'] == result.json['total'] == 1
