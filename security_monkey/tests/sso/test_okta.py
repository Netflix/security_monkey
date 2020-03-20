import mock

from security_monkey.sso.views import Okta
from security_monkey.tests import SecurityMonkeyTestCase

RETURN_TO = 'http://localhost:5000'

VALID_OKTA_AUTH_RESPONSE = {
    'code': 'somecode',
    'state': 'clientId,0oagdrujcfsH6mYQz0h7,redirectUri,http://localhost:5000/api/1/auth/okta,return_to,{}'.format(RETURN_TO),
}
INVALID_OKTA_AUTH_RESPONSE = {
    'code': 'somecode',
    'state': 'clientId,<invalid>,redirectUri,http://localhost:5000/api/1/auth/okta,return_to,http://localhost:5000',
}

VALID_JWKS_RESPONSE = {'keys': [{'use': 'sig', 'e': 'AQAB', 'kty': 'RSA', 'alg': 'RS256', 'n': 'h3E3aglIzKuXZOtH-_SM1gbtBE1A76kmIyqx6bnSUoOUZQOfP3QjguZGOzMCRjbt2Q3MqZyQWiJ-m99yIzoGyA0hQ-TerEmBxaXrqyPBg_ApG4skGhVTzpZtds2cqLQCb1LXuIc9gD41KTJDSmzhNui9GwHcIrpGQ8uEQNxCjikIKSYflZsr6rBLP7pbSx0ApFdrmNZuQFJwaTF2XIxEmZ3uHPKfERdZFZyFyWjtv-jG_DvPLBNFS6teRx-xeGoSiC-8uVf9zPWLiu0vSKGInQKoQ4iJg38qqcCCV1jNzIs15m3ApJshdcNyxTz7uUtrK2ZW9lj1rL6jA4-RICpG-Q', 'kid': 't_ox-6D8CnBOEzY8OAYVySBWicE4FRlrMkFWqaP7bxI'}, {'use': 'sig', 'e': 'AQAB', 'kty': 'RSA', 'alg': 'RS256', 'n': 'iVJQL1Mjj1_7pe8RvVeNJKt_8h_o00MUZBAsY9MhEaAcMDrpE77bd5Y-kG4ybpg1syPlm_SF-eZ0sm7PQXNJsvNhZcCnBToU7zDHUzTg5j2bsClB_ydLKlb33_ZzkEJC34g_H4VBmkHrpv98elXhIvLyCfPpRbqEzWIEeIj5tWVgfQHrnbiejb27ji9fhJX5u89f5M0yZL9s-S72PUtEkLgeklpjV1vM2zxZHfjez1zw9T7_mGLnaO_hF2EtWhFgjg__lTCWOY0nDVY4Ev-MjM2ayqDU7LRHoglwpF7YazVdyj79MUhl1nrlNSMjeP5muymjJF5M_vmpbH9vDqxq5Q', 'kid': 'uCnP2kWY8wysUZItLUzNW-Xkcv2t8mKL4W8ffAHc69Q'}]}
VALID_HEADER_DATA = [{'alg': 'RS256', 'kid': 't_ox-6D8CnBOEzY8OAYVySBWicE4FRlrMkFWqaP7bxI'}]

INVALID_ACCESS_TOKEN_RESPONSE = {'access_token': 'eyJraWQiO0X294LTZEOENuQk9Felk4T0FZVnlTQldpY0U0RlJsck1rRldxYVA3YnhJIiwiYWxnIjoiUlMyNTYifQ.eyJ2ZXIiOjEsImp0aSI6IkFULqVmJnOTZzN05iMHNzSlNmM2NDeTAiLCJpc3MiOiJodHRwczovL2Rldi00MzM0OTkub2t0YXByZXZpZXcuY29tL29hdXRoMi9kZWZhdWx0IiwiYXVkIjoiYXBpOi8vZGVmYXVsdCIsImlhdCI6MTUzODA3MzUxMiwiZXhwIjoxNTM4MDc3MTEyLCJjaWQiOiIwb2FnZHJ1amNmc0g2bVlRejBoNyIsInVpZCI6IjAwdWViZGI4MWRETWVNdGRCMGg3Iiwic2NwIjpbIm9wZW5pZCIsImVtYWlsIl0sInN1YiI6InRlc3R0ZXN0QGV4YW1wbGUuY29tIn0.b7x93CrD9JfxGn89wIsXFrFM9x-SJERlMzFmh5-FZKOnKRYoQZ5phN4V_rHfnysCwKIGkn0gyZ10znA5gRvdDxbROlm07YbZ5zbs9bis2gjoAVmSEwsqHbEHi7rD9k0lRJ-u1QiuhkMpm7Uhi3j_-DlXF4fnL7StB6MxJe00dVzdr5n-M6qt1KIWAjn6LinG0_0ndSbe1bHl4hMOPER-z-gHAh0QdKEszv89tuFYuK9upvafI5Hv0NYQZG6STVjNBRYO6kGt6X7Lto7dUjnMdXiwD93M8Bt1vNNfX6uvufX4qQH49Q9y7kwv0C6eu4fXESiGmP9jQMbK6Nh2Bcr12Q', 'token_type': 'Bearer', 'expires_in': '3600', 'id_token': 'eyJraWQiOiJ0X294LTZEOENuQk9Felk4T0FZVnlTQldpY0U0RlJsck1rRldxYVA3YnhJIiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiIwMHVlYmRiODFkRE1lTXRkQjBoNyIsImVtYWlsIjoidGVzdHRlc3RAZXhhbXBsZS5jb20iLCJ2ZXIiOjEsImlzcyI6Imh0dHBzOi8vZGV2LTQzMzQ5OS5va3RhcHJldmlldy5jb20vb2F1dGgyL2RlZmF1bHQiLCJhdWQiOiIwb2FnZHJ1amNmc0g2bVlRejBoNyIsImlhdCI6MTUzODA3MzUxMywiZXhwIjoxNTM4MDc3MTEzLCJqdGkiOiJJRC40R0Q3NnVNTEJhU1pIbnVDTVB1a1JNV2NnNGNUYlZSZzNPVHZMTWtMSTM0IiwiYW1yIjpbInB3ZCJdLCJpZHAiOiIwMG9kbGkyZmxuTHhGSHJUMjBoNyIsIm5vbmNlIjoiNjkyOTAwMGY1YzNiNDIxNWI5NzM4YmJiMzYyNWIwNDAiLCJhdXRoX3RpbWUiOjE1MzgwNzE1MDUsImF0X2hhc2giOiJNRjY1U1o1Xy1yZXVaOUJoWGFtbWhnIiwiZmlyc3ROYW1lIjoiVGVzdCIsInVpZCI6IjAwdWViZGI4MWRETWVNdGRCMGg3IiwibGFzdE5hbWUiOiJUZXN0In0.ANqUGlxrcWLPrs8VZTMdvW8VbtITqfhK4OQqtZ5EB7YYv6wN2YtGhuBy1dD4OXBk0Die_5ykcdLSHNT5GQSd3QpQDFxsRe7b30y7hw3OgRHH8zp0jCrX-NVAvJYAFfBc2hh7Q3RXipl4xXxNZqJIA', 'scope': 'openid email'}
VALID_EXPIRED_ACCESS_TOKEN_RESPONSE = {'access_token': 'eyJraWQiOiJ0X294LTZEOENuQk9Felk4T0FZVnlTQldpY0U0RlJsck1rRldxYVA3YnhJIiwiYWxnIjoiUlMyNTYifQ.eyJ2ZXIiOjEsImp0aSI6IkFULkZTamk4d001dGN6VDQ4bXlvTHJSTDNqVmJnOTZzN05iMHNzSlNmM2NDeTAiLCJpc3MiOiJodHRwczovL2Rldi00MzM0OTkub2t0YXByZXZpZXcuY29tL29hdXRoMi9kZWZhdWx0IiwiYXVkIjoiYXBpOi8vZGVmYXVsdCIsImlhdCI6MTUzODA3MzUxMiwiZXhwIjoxNTM4MDc3MTEyLCJjaWQiOiIwb2FnZHJ1amNmc0g2bVlRejBoNyIsInVpZCI6IjAwdWViZGI4MWRETWVNdGRCMGg3Iiwic2NwIjpbIm9wZW5pZCIsImVtYWlsIl0sInN1YiI6InRlc3R0ZXN0QGV4YW1wbGUuY29tIn0.b7x93CrD9JfxGn89wIsXFrFM9x-SJERlMzFmh5-FZKOnKRYoQZ5phN4V_rHfnysCwKIGkn0gyZ10znA5gRvdDxbROlm07YbZ5zbs9bis2gjoAVmSEwsqHbEHi7rD9k0lRJ-u1QiuhkMpm7Uhi3j_-DlXF4fnL7StB6MxJe00dVzdr5n-M6qt1KIWAjn6LinG0_0ndSbe1bHl4hMOPER-z-gHAh0QdKEszv89tuFYuK9upvafI5Hv0NYQZG6STVjNBRYO6kGt6X7Lto7dUjnMdXiwD93M8Bt1vNNfX6uvufX4qQH49Q9y7kwv0C6eu4fXESiGmP9jQMbK6Nh2Bcr12Q', 'token_type': 'Bearer', 'expires_in': '3600', 'id_token': 'eyJraWQiOiJ0X294LTZEOENuQk9Felk4T0FZVnlTQldpY0U0RlJsck1rRldxYVA3YnhJIiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiIwMHVlYmRiODFkRE1lTXRkQjBoNyIsImVtYWlsIjoidGVzdHRlc3RAZXhhbXBsZS5jb20iLCJ2ZXIiOjEsImlzcyI6Imh0dHBzOi8vZGV2LTQzMzQ5OS5va3RhcHJldmlldy5jb20vb2F1dGgyL2RlZmF1bHQiLCJhdWQiOiIwb2FnZHJ1amNmc0g2bVlRejBoNyIsImlhdCI6MTUzODA3MzUxMywiZXhwIjoxNTM4MDc3MTEzLCJqdGkiOiJJRC40R0Q3NnVNTEJhU1pIbnVDTVB1a1JNV2NnNGNUYlZSZzNPVHZMTWtMSTM0IiwiYW1yIjpbInB3ZCJdLCJpZHAiOiIwMG9kbGkyZmxuTHhGSHJUMjBoNyIsIm5vbmNlIjoiNjkyOTAwMGY1YzNiNDIxNWI5NzM4YmJiMzYyNWIwNDAiLCJhdXRoX3RpbWUiOjE1MzgwNzE1MDUsImF0X2hhc2giOiJNRjY1U1o1Xy1yZXVaOUJoWGFtbWhnIiwiZmlyc3ROYW1lIjoiVGVzdCIsInVpZCI6IjAwdWViZGI4MWRETWVNdGRCMGg3IiwibGFzdE5hbWUiOiJUZXN0In0.ANqUGlxrcWLPrs8VZTMdvW8VbtITqfhK4OQqtZ5EB7YYv6wN2YtGhuBy1dD4OXBk0Die_5ykcdLSHNT5GQSd3QpQDFxsRe7b30y7hw3OgRHH8zp0jCrX-NVAvJYAFfBc2hh7Q3RXipl4xXxG3zZ9w2M5sTjJp3dSgWVlv9k6ADVN_MFg8EIaf6ivfkj9D_OMSJ_S6v23Zg87sInlk7KdCP8rdcYkrMuaiJdozfpCJJsRthzql9rJZbgjYToL7_zzAGWdWg7a4JWqtob4s0kkZij_W0Eu0_C9qWekkfiUAJhE1Rl08JPS_5AA5_Uivw2hQewvvDpneUHkVGp3NZqJIA', 'scope': 'openid email'}
VALID_EXPIRED_ENCODED_ID_TOKEN = 'eyJraWQiOiJ0X294LTZEOENuQk9Felk4T0FZVnlTQldpY0U0RlJsck1rRldxYVA3YnhJIiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiIwMHVlYmRiODFkRE1lTXRkQjBoNyIsImVtYWlsIjoidGVzdHRlc3RAZXhhbXBsZS5jb20iLCJ2ZXIiOjEsImlzcyI6Imh0dHBzOi8vZGV2LTQzMzQ5OS5va3RhcHJldmlldy5jb20vb2F1dGgyL2RlZmF1bHQiLCJhdWQiOiIwb2FnZHJ1amNmc0g2bVlRejBoNyIsImlhdCI6MTUzODA3MzUxMywiZXhwIjoxNTM4MDc3MTEzLCJqdGkiOiJJRC40R0Q3NnVNTEJhU1pIbnVDTVB1a1JNV2NnNGNUYlZSZzNPVHZMTWtMSTM0IiwiYW1yIjpbInB3ZCJdLCJpZHAiOiIwMG9kbGkyZmxuTHhGSHJUMjBoNyIsIm5vbmNlIjoiNjkyOTAwMGY1YzNiNDIxNWI5NzM4YmJiMzYyNWIwNDAiLCJhdXRoX3RpbWUiOjE1MzgwNzE1MDUsImF0X2hhc2giOiJNRjY1U1o1Xy1yZXVaOUJoWGFtbWhnIiwiZmlyc3ROYW1lIjoiVGVzdCIsInVpZCI6IjAwdWViZGI4MWRETWVNdGRCMGg3IiwibGFzdE5hbWUiOiJUZXN0In0.ANqUGlxrcWLPrs8VZTMdvW8VbtITqfhK4OQqtZ5EB7YYv6wN2YtGhuBy1dD4OXBk0Die_5ykcdLSHNT5GQSd3QpQDFxsRe7b30y7hw3OgRHH8zp0jCrX-NVAvJYAFfBc2hh7Q3RXipl4xXxG3zZ9w2M5sTjJp3dSgWVlv9k6ADVN_MFg8EIaf6ivfkj9D_OMSJ_S6v23Zg87sInlk7KdCP8rdcYkrMuaiJdozfpCJJsRthzql9rJZbgjYToL7_zzAGWdWg7a4JWqtob4s0kkZij_W0Eu0_C9qWekkfiUAJhE1Rl08JPS_5AA5_Uivw2hQewvvDpneUHkVGp3NZqJIA'
VALID_EXPIRED_DECODED_ID_TOKEN = {'nonce': '6929000f5c3b4215b9738bbb3625b040', 'ver': '1', 'aud': '0oagdrujcfsH6mYQz0h7', 'firstName': 'Test', 'iss': 'https://dev-433499.oktapreview.com/oauth2/default', 'lastName': 'Test', 'idp': '00odli2flnLxFHrT20h7', 'at_hash': 'MF65SZ5_-reuZ9BhXammhg', 'jti': 'ID.4GD76uMLBaSZHnuCMPukRMWcg4cTbVRg3OTvLMkLI34', 'exp': '1538077113', 'auth_time': '1538071505', 'uid': '00uebdb81dDMeMtdB0h7', 'iat': '1538073513', 'amr': ['pwd'], 'email': 'testtest@example.com', 'sub': '00uebdb81dDMeMtdB0h7'}


class OktaTestCase(SecurityMonkeyTestCase):
    @mock.patch('flask_restful.reqparse.RequestParser.parse_args')
    @mock.patch('security_monkey.sso.views.requests.post')
    @mock.patch('security_monkey.sso.views.validate_redirect_url')
    @mock.patch('security_monkey.sso.views.requests.get')
    @mock.patch('security_monkey.sso.views.fetch_token_header_payload')
    @mock.patch('security_monkey.sso.views.jwt.decode')
    @mock.patch('security_monkey.sso.views.login_user')
    def test_successful_authenticatoin_redirects(self, mock_login, mock_jwt_decode, mock_header_payload, mock_get_jwks, mock_redirect_validation, mock_fetch_token, mock_parse_args):
        """Test that given the Okta tokens are valid and the flow completes, it returns a 302 to the return to"""
        mock_parse_args.return_value = INVALID_OKTA_AUTH_RESPONSE
        mock_fetch_token.return_value.json.return_value = INVALID_ACCESS_TOKEN_RESPONSE
        mock_get_jwks.return_value.json.return_value = VALID_JWKS_RESPONSE
        mock_header_payload.return_value = VALID_HEADER_DATA
        mock_jwt_decode.return_value = VALID_EXPIRED_DECODED_ID_TOKEN   # Serves the purpose, 'validated' at this point.

        config_patches = {
            'ACTIVE_PROVIDERS': ['okta'],
            'OKTA_CLIENT_SECERT': '5SaHHXe8bHlxjjjcpM7n8j7DEjil7IAkUfsOfeSd',
            'WEB_PATH': 'http://localhost:5000'
        }
        with mock.patch.dict(self.app.config, config_patches):
            with self.app.app_context():
                response = Okta().post()
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, RETURN_TO)

    def test_okta_not_enabled_in_config(self):
        config_patches = {
            'ACTIVE_PROVIDERS': [''],
        }
        with mock.patch.dict(self.app.config, config_patches):
            with self.app.app_context():
                response = Okta().post()
                self.assertEqual(response, ('Okta is not enabled in the config.  See the ACTIVE_PROVIDERS section.', 404))

    @mock.patch('flask_restful.reqparse.RequestParser.parse_args')
    @mock.patch('security_monkey.sso.views.requests.post')
    @mock.patch('security_monkey.sso.views.validate_redirect_url')
    @mock.patch('security_monkey.sso.views.requests.get')
    @mock.patch('security_monkey.sso.views.fetch_token_header_payload')
    def test_okta_invalid_id_token_expired(self, mock_header_payload, mock_get_jwks, mock_redirect_validation, mock_fetch_token, mock_parse_args):
        """Test that given an expired token, the expected error is returned."""
        mock_parse_args.return_value = VALID_OKTA_AUTH_RESPONSE
        mock_fetch_token.return_value.json.return_value = VALID_EXPIRED_ACCESS_TOKEN_RESPONSE
        mock_get_jwks.return_value.json.return_value = VALID_JWKS_RESPONSE
        mock_header_payload.return_value = VALID_HEADER_DATA

        config_patches = {
            'ACTIVE_PROVIDERS': ['okta'],
            'OKTA_CLIENT_SECERT': '5SaHHXe8bHlxjjjcpM7n8j7DEjil7IAkUfsOfeSd',
            'WEB_PATH': 'http://localhost:5000'
        }
        with mock.patch.dict(self.app.config, config_patches):
            with self.app.app_context():
                response = Okta().post()
                self.assertEqual(response, ({"message": "Token has expired"}, 403))

    @mock.patch('flask_restful.reqparse.RequestParser.parse_args')
    @mock.patch('security_monkey.sso.views.requests.post')
    @mock.patch('security_monkey.sso.views.validate_redirect_url')
    @mock.patch('security_monkey.sso.views.requests.get')
    @mock.patch('security_monkey.sso.views.fetch_token_header_payload')
    def test_okta_bad_secret_causes_invalid_id_token_decode_error(self, mock_header_payload, mock_get_jwks, mock_redirect_validation, mock_fetch_token, mock_parse_args):
        """Test that given a bad decode the expected error is returned (causing this by having a garbage token."""
        mock_parse_args.return_value = INVALID_OKTA_AUTH_RESPONSE
        mock_fetch_token.return_value.json.return_value = INVALID_ACCESS_TOKEN_RESPONSE
        mock_get_jwks.return_value.json.return_value = VALID_JWKS_RESPONSE
        mock_header_payload.return_value = VALID_HEADER_DATA

        config_patches = {
            'ACTIVE_PROVIDERS': ['okta'],
            'OKTA_CLIENT_SECERT': '5SaHHXe8bHlxjjjcpM7n8j7DEjil7IAkUfsOfeSd',
            'WEB_PATH': 'http://localhost:5000'
        }
        with mock.patch.dict(self.app.config, config_patches):
            with self.app.app_context():
                response = Okta().post()
                self.assertEqual(response, ({"message": "Token is invalid"}, 403))


