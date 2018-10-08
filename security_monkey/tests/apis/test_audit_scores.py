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
.. module: security_monkey.tests.apis.test_audit_scores
    :platform: Unix
.. version:: $$VERSION$$
.. moduleauthor::  Mike Grima <mgrima@netflix.com>
"""
import json

from security_monkey.tests.apis.conftest import make_auth_header


def test_fixtures(audit_overrides):
    from security_monkey.datastore import ItemAuditScore

    items = ItemAuditScore.query.all()

    for override in items:
        assert override.technology in audit_overrides
        assert override.score == audit_overrides[override.technology]['score']
        assert override.method == audit_overrides[override.technology]['method']
        assert override.disabled == audit_overrides[override.technology].get('disabled', False)

    assert len(items) == 3


def test_get_all_audit_scores(client, user_tokens, audit_overrides):
    from security_monkey.views.audit_scores import AuditScoresGet, api

    # No Auth:
    assert client.get(api.url_for(AuditScoresGet)).status_code == 401

    # With all users:
    for t in user_tokens.values():
        result = client.get(api.url_for(AuditScoresGet), headers=make_auth_header(t))

        assert result.status_code == 200
        assert result.json['count'] == result.json['total'] == len(audit_overrides) == \
            len(result.json['items'])
        assert result.json['page'] == 1

        for item in result.json['items']:
            assert item['score'] == audit_overrides[item['technology']]['score']
            assert item['method'] == audit_overrides[item['technology']]['method']
            assert item['disabled'] == audit_overrides[item['technology']].get('disabled', False)
            assert item['id']


def test_post_audit_score(client, user_tokens):
    from security_monkey.views.audit_scores import AuditScoresGet, api
    from security_monkey.datastore import ItemAuditScore

    # No Auth:
    assert client.post(api.url_for(AuditScoresGet)).status_code == 401

    # With all users:
    for user, token in user_tokens.items():
        data = {
            'technology': 's3',
            'score': 0,
            'method': 'check_root_cross_account',
            'disabled': True
        }

        result = client.post(api.url_for(AuditScoresGet), data=json.dumps(data), headers=make_auth_header(token))

        if user == 'admin@securitymonkey':
            assert result.status_code == 201
            db_item = ItemAuditScore.query.filter(ItemAuditScore.technology == 's3',
                                                  ItemAuditScore.method == 'check_root_cross_account').one()

            assert db_item
            for key, value in data.items():
                assert getattr(db_item, key) == data[key]

            # And again:
            data['disabled'] = False
            data['score'] = 10
            result = client.post(api.url_for(AuditScoresGet), data=json.dumps(data), headers=make_auth_header(token))
            assert result.status_code == 201
            assert db_item
            for key, value in data.items():
                assert getattr(db_item, key) == data[key]

            # Test that if any of the required fields are missing, it should return a 400:
            for field in data.keys():
                new_data = dict(data)
                new_data.pop(field)
                assert client.post(api.url_for(AuditScoresGet), data=json.dumps(new_data),
                                   headers=make_auth_header(token)).status_code == 400

            # No JSON:
            assert client.post(api.url_for(AuditScoresGet), headers=make_auth_header(token)).status_code == 400

        else:
            assert result.status_code == 403


def test_get_audit_score_by_id(client, user_tokens, audit_overrides):
    from security_monkey.views.audit_scores import AuditScoreGetPutDelete, api
    from security_monkey.datastore import ItemAuditScore

    # No Auth:
    assert client.get(api.url_for(AuditScoreGetPutDelete, id=1)).status_code == 401

    # Get all ItemAuditScores to query:
    items = ItemAuditScore.query.all()

    # For all users:
    for token in user_tokens.values():
        for item in items:
            result = client.get(api.url_for(AuditScoreGetPutDelete, id=item.id), headers=make_auth_header(token))

            assert result.status_code == 200

            for key, value in result.json.items():
                assert getattr(item, key) == value

        assert client.get(api.url_for(AuditScoreGetPutDelete, id=99),
                          headers=make_auth_header(token)).status_code == 404


def test_delete_audit_score_by_id(client, user_tokens, audit_overrides):
    from security_monkey.views.audit_scores import AuditScoreGetPutDelete, api
    from security_monkey.datastore import ItemAuditScore

    # No Auth:
    assert client.delete(api.url_for(AuditScoreGetPutDelete, id=1)).status_code == 401

    # Get all ItemAuditScores to query:
    items = ItemAuditScore.query.all()

    # For all users:
    for user, token in user_tokens.items():
        for item in items:
            result = client.delete(api.url_for(AuditScoreGetPutDelete, id=item.id), headers=make_auth_header(token))

            if user == 'admin@securitymonkey':
                assert result.status_code == 202

                # And again:
                assert client.delete(api.url_for(AuditScoreGetPutDelete, id=item.id),
                                     headers=make_auth_header(token)).status_code == 404

            else:
                assert result.status_code == 403
