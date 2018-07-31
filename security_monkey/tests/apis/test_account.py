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
import json


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
    result = client.get(api.url_for(AccountPostList, active=False, third_party=False), headers=make_auth_header(t))
    assert result.status_code == 200
    assert len(result.json['items']) == result.json['count'] == result.json['total'] == 1


def test_post_new_account(client, user_tokens, test_aws_accounts):
    from security_monkey.views.account import AccountPostList, api

    # No Auth:
    assert client.post(api.url_for(AccountPostList)).status_code == 401

    # With no data:
    assert client.post(api.url_for(AccountPostList),
                       headers=make_auth_header(user_tokens['admin@securitymonkey'])).status_code == 400

    data = {
        'name': 'bananas',
        'identifier': '888888888888',
        'account_type': 'AWS',
        'notes': 'Security Monkey is awesome',
        'active': True,
        'third_party': False,
        'custom_fields': {
            'canonical_id': '1023984012398098123urjhoisjdkfaklsdjfaoweu239084',
            's3_name': 'bananas'
        }
    }

    # New account named 'bananas'
    result = client.post(api.url_for(AccountPostList), data=json.dumps(data),
                         headers=make_auth_header(user_tokens['admin@securitymonkey']))

    assert result.status_code == 201

    # Verify data is correct:
    cf = data.pop('custom_fields')
    for i, v in data.items():
        assert v == result.json[i]

    assert not result.json['custom_fields']['role_name']
    for i, v in cf.items():
        assert v == result.json['custom_fields'][i]

    # And again...
    assert client.post(api.url_for(AccountPostList), data=json.dumps(data),
                       headers=make_auth_header(user_tokens['admin@securitymonkey'])).status_code == 400

    # With invalid account type:
    data['account_type'] = 'FAILURE'
    assert client.post(api.url_for(AccountPostList), data=json.dumps(data),
                       headers=make_auth_header(user_tokens['admin@securitymonkey'])).status_code == 400

    # With insufficient creds:
    assert client.post(api.url_for(AccountPostList), data=json.dumps(data),
                         headers=make_auth_header(user_tokens['justify@securitymonkey'])).status_code == 403
