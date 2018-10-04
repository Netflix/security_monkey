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


def test_fixtures(aws_test_accounts):
    from security_monkey.datastore import Account

    accounts = Account.query.all()
    assert len(accounts) == 5

    for a in accounts:
        assert a.type.name == "AWS"


def test_get_all_accounts(client, user_tokens, aws_test_accounts):
    from security_monkey.views.account import AccountPostList, api

    # No Auth:
    assert client.get(api.url_for(AccountPostList)).status_code == 401

    # With all users:
    for t in user_tokens.values():
        result = client.get(api.url_for(AccountPostList), headers=make_auth_header(t))
        assert result.status_code == 200

        assert len(result.json['items']) == len(aws_test_accounts) == result.json['total'] \
            == result.json['count']

    # 3rd party only:
    result = client.get(api.url_for(AccountPostList, third_party=True), headers=make_auth_header(t))
    assert result.status_code == 200
    assert len(result.json['items']) == result.json['count'] == result.json['total'] == 2

    # Inactive but first party:
    result = client.get(api.url_for(AccountPostList, active=False, third_party=False), headers=make_auth_header(t))
    assert result.status_code == 200
    assert len(result.json['items']) == result.json['count'] == result.json['total'] == 1


def test_post_new_account(client, user_tokens, aws_test_accounts):
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
                       headers=make_auth_header(user_tokens['admin@securitymonkey'])).status_code == 409

    # With invalid account type:
    data['account_type'] = 'FAILURE'
    assert client.post(api.url_for(AccountPostList), data=json.dumps(data),
                       headers=make_auth_header(user_tokens['admin@securitymonkey'])).status_code == 400

    # With insufficient creds:
    user_tokens.pop('admin@securitymonkey')
    for t in user_tokens.values():
        assert client.post(api.url_for(AccountPostList), data=json.dumps(data),
                           headers=make_auth_header(t)).status_code == 403


def test_account_get_put_delete_api(client, user_tokens, aws_test_accounts):
    from security_monkey.views.account import AccountGetPutDelete, api
    from security_monkey.datastore import Account

    # No Auth:
    assert client.get(api.url_for(AccountGetPutDelete, account_id=1)).status_code == 401
    assert client.put(api.url_for(AccountGetPutDelete, account_id=1)).status_code == 401
    assert client.delete(api.url_for(AccountGetPutDelete, account_id=1)).status_code == 401

    # Get the account's details from the DB:
    account = Account.query.filter(Account.id == 1).first().get_dict()
    cf = account.pop('custom_fields')

    # Test Get/Put for all user types:
    for user, token in user_tokens.items():
        # Test GET:
        result = client.get(api.url_for(AccountGetPutDelete, account_id=1), headers=make_auth_header(token))
        assert result.status_code == 200

        for i, v in account.items():
            assert result.json[i] == v

        for i, v in cf.items():
            assert result.json['custom_fields'][i] == v

        # And an invalid account ID for GET:
        assert client.get(api.url_for(AccountGetPutDelete, account_id=99),
                          headers=make_auth_header(token)).status_code == 404

        # Test PUT:
        put_data = dict(account)

        put_data['notes'] = 'Some account for testing Security Monkey'
        put_data['custom_fields'] = {'role_name': 'some_role_for_testing'}

        result = client.put(api.url_for(AccountGetPutDelete, account_id=account['id']), data=json.dumps(put_data),
                            headers=make_auth_header(token))

        if user == 'admin@securitymonkey':
            assert result.status_code == 200

            assert put_data['notes'] == result.json['notes']
            assert put_data['custom_fields']['role_name'] == result.json['custom_fields']['role_name']

            # And an invalid account ID for Put:
            assert client.put(api.url_for(AccountGetPutDelete, account_id=99), data=json.dumps(put_data),
                              headers=make_auth_header(token)).status_code == 404

            # Restore the data back:
            put_data = dict(account)
            put_data['custom_fields'] = cf
            client.put(api.url_for(AccountGetPutDelete, account_id=account['id']), data=json.dumps(put_data),
                       headers=make_auth_header(token))

        else:
            assert result.status_code == 403

    # Test Delete for all User types:
    for user, token in user_tokens.items():
        result = client.delete(api.url_for(AccountGetPutDelete, account_id=account['id']),
                               headers=make_auth_header(token))

        if user == 'admin@securitymonkey':
            assert result.status_code == 202
            assert result.json['status'] == 'deleted'

        else:
            assert result.status_code == 403
