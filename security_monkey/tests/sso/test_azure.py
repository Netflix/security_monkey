#     Copyright 2017 Netflix, Inc.
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
.. module: security_monkey.tests.sso.test_azure
    :platform: Unix
.. version:: $$VERSION$$
.. moduleauthor::  Juan Leaniz <juan.leaniz@ubisoft.com>
"""

from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.sso.views import AzureAD

TEST_CONFIG = {
    'clientID': '8d24cc89-0f6c-44aa-82c4-6b483f00cbb5',
    'jwksUrl': 'https://login.microsoftonline.com/common/discovery/keys'
}

decoded_id_token = {u'nonce': u'd9cf2561563e4ec3bc18ea3373bad543', u'family_name': u'Leaniz', u'sub': u'ISSDOLYIFn5GPZBN0S6PfdBx-haA2KVK4lLZbci3C-s', u'c_hash': u'y_9iMybdDKd7iEN4w_14iw', u'aud': u'8d24cc89-0f6c-44aa-82c4-xxxxxxxx', u'iss': u'https://sts.windows.net/6a1af301-b747-43c1-80ac-xxxxxxxx/', u'oid': u'5b32bcc6-b57d-4914-9074-2c8a17c18abe', u'ipaddr': u'10.11.11.1', u'unique_name': u'juan.leaniz_ubisoft.com#EXT#@ubisoftsrm.onmicrosoft.com', u'idp': u'https://sts.windows.net/e01bd386-fa51-4210-a2a4-xxxx/', u'email': u'juan.leaniz_ubisoft.com#EXT#@ubisoftsrm.onmicrosoft.com', u'aio': u'ATQAy/8EAAAAFhmfvc4rjeMQ3f2xFN0/g0+ea8ss3n9mUH/xT9HDtA6qsIt84FFK1h7gNRSaJz4S', u'given_name': u'Juan', u'exp': 1504811806, u'in_corp': u'true', u'tid': u'6a1af301-b747-43c1-80ac-4e944b56b779', u'iat': 1504807906, u'amr': [u'wia'], u'nbf': 1504807906, u'ver': u'1.0', u'name': u'Juan Leaniz'}

encoded_id_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IkhIQnlLVS0wRHFBcU1aaDZaRlBkMlZXYU90ZyIsImtpZCI6IkhIQnlLVS0wRHFBcU1aaDZaRlBkMlZXYU90ZyJ9.eyJhdWQiOiI4ZDI0Y2M4OS0wZjZjLTQ0YWEtODJjNC02YjQ4M2YwMGNiYjUiLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC82YTFhZjMwMS1iNzQ3LTQzYzEtODBhYy00ZTk0NGI1NmI3NzkvIiwiaWF0IjoxNTA0ODA3OTA2LCJuYmYiOjE1MDQ4MDc5MDYsImV4cCI6MTUwNDgxMTgwNiwiYWlvIjoiQVRRQXkvOEVBQUFBRmhtZnZjNHJqZU1RM2YyeEZOMC9nMCtlYThzczNuOW1VSC94VDlIRHRBNnFzSXQ4NEZGSzFoN2dOUlNhSno0UyIsImFtciI6WyJ3aWEiXSwiY19oYXNoIjoieV85aU15YmRES2Q3aUVONHdfMTRpdyIsImVtYWlsIjoianVhbi5sZWFuaXpfdWJpc29mdC5jb20jRVhUI0B1Ymlzb2Z0c3JtLm9ubWljcm9zb2Z0LmNvbSIsImZhbWlseV9uYW1lIjoiTGVhbml6IiwiZ2l2ZW5fbmFtZSI6Ikp1YW4iLCJpZHAiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC9lMDFiZDM4Ni1mYTUxLTQyMTAtYTJhNC0yOWU1YWI2ZjdhYjEvIiwiaW5fY29ycCI6InRydWUiLCJpcGFkZHIiOiIxOTguMTYuMjQzLjYiLCJuYW1lIjoiSnVhbiBMZWFuaXoiLCJub25jZSI6ImQ5Y2YyNTYxNTYzZTRlYzNiYzE4ZWEzMzczYmFkNTQzIiwib2lkIjoiNWIzMmJjYzYtYjU3ZC00OTE0LTkwNzQtMmM4YTE3YzE4YWJlIiwic3ViIjoiSVNTRE9MWUlGbjVHUFpCTjBTNlBmZEJ4LWhhQTJLVks0bExaYmNpM0MtcyIsInRpZCI6IjZhMWFmMzAxLWI3NDctNDNjMS04MGFjLTRlOTQ0YjU2Yjc3OSIsInVuaXF1ZV9uYW1lIjoianVhbi5sZWFuaXpfdWJpc29mdC5jb20jRVhUI0B1Ymlzb2Z0c3JtLm9ubWljcm9zb2Z0LmNvbSIsInZlciI6IjEuMCJ9.OvAfv-PNTkeRkcSiM_ZtXFrxIYD6NDiStgXRaNKjqzcNYUJsLpVll_ZRI_uY1Hmj3FTqHMTF2J7piLHQFzXDDte8dJYCG-WpysQWOTJdd5cml2_-dSqqPnYAGI6f6uG23KgGQJb-xKTRWXRz42od6xukKcWRCwTZDu6P_cCATFiMrccQNpeV2_OuzzmAXCZ-EbY4EyJmBjwhHF6hdNZqdH95omurCutyhSgg0tv5oU-YJlHVVw1al2136mD4l0biO53yAJ2WjOW7tYFBLva3W8XDuhFberk-4JauwnsaEejL476ZF64ssIzNwuzh00OOngEx2UXKUneOaEqzhXCjuA'

fake_keys_response = {
  "keys": [
    {
      "kty": "RSA",
      "use": "sig",
      "kid": "HHByKU-0DqAqMZh6ZFPd2VWaOtg",
      "x5t": "HHByKU-0DqAqMZh6ZFPd2VWaOtg",
      "n": "1V3C8iuyrUY_7HMyDWisNGLa5GEEkvCczQtQqTH3Mr0P4hyw2usihJuh3Q_eop5juZR3oy_HTVsVbDvLVkZ7BZZ4-M4UhcNARooYg3RZcdZymasHbVW5GBGvpGetW8pUmVniCYV2R9UZjWmdGpPO2O_2UrkNpOuiceeFEvAZqOsodWc28yo5VhsIlAUPqkJOh5XnpGUP2p49VVhKlm6XmQsaRcius1urXT3gp3W_7TtHpiJ8XD06L5i8hdBXybMZrO8uGfEkUH5Nc8HCqNA4POiCTq_N_P0NkYrGEpgMeH4oHTVhYq5eh-8MaopmsLiZgC3tNkZri0wI3DBL8Xrlrw",
      "e": "AQAB",
      "x5c": [
        "MIIDBTCCAe2gAwIBAgIQLplyYn9yyqlCiJ/PVTna6TANBgkqhkiG9w0BAQsFADAtMSswKQYDVQQDEyJhY2NvdW50cy5hY2Nlc3Njb250cm9sLndpbmRvd3MubmV0MB4XDTE3MDcyNzAwMDAwMFoXDTE5MDcyODAwMDAwMFowLTErMCkGA1UEAxMiYWNjb3VudHMuYWNjZXNzY29udHJvbC53aW5kb3dzLm5ldDCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBANVdwvIrsq1GP+xzMg1orDRi2uRhBJLwnM0LUKkx9zK9D+IcsNrrIoSbod0P3qKeY7mUd6Mvx01bFWw7y1ZGewWWePjOFIXDQEaKGIN0WXHWcpmrB21VuRgRr6RnrVvKVJlZ4gmFdkfVGY1pnRqTztjv9lK5DaTronHnhRLwGajrKHVnNvMqOVYbCJQFD6pCToeV56RlD9qePVVYSpZul5kLGkXIrrNbq1094Kd1v+07R6YifFw9Oi+YvIXQV8mzGazvLhnxJFB+TXPBwqjQODzogk6vzfz9DZGKxhKYDHh+KB01YWKuXofvDGqKZrC4mYAt7TZGa4tMCNwwS/F65a8CAwEAAaMhMB8wHQYDVR0OBBYEFJnvdZTJC0SLogTiajqLhDJabFtUMA0GCSqGSIb3DQEBCwUAA4IBAQAq9cwse+hSpZ/19bX54EftSJkpgAeV3RoVX/y+zCfH8hvOKYFKiNucx7k32KNGxnfaSkkMQ/xtJWxwQhFg93/n+YfjEg3bljW5tAQ3CgaB+h3h9EEDnUAHh7Tv3W4X4/hbqRa6NiTJWVUFRM7KDY3wwXaxttfyVAG6F9zmJZaqvsNFxrSnG+Pg+B1B+YtBYy0aeUoI7kSTx++WLtcKLlb+Ie5j26QOijsLCp/4vWi3OBuZptexgTmTCeQpCU7NLKiZZdN6076+lHJYYhTENjuoIP74KZnoJxBTHpp3iR0GpmR66ssCSL2LHBug3GmBaJ32EyC1AifOWLudp1M8/nn2"
      ]
    }
  ]
}

secret = "-----BEGIN PUBLIC KEY-----"
"MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1V3C8iuyrUY/7HMyDWis"
"NGLa5GEEkvCczQtQqTH3Mr0P4hyw2usihJuh3Q/eop5juZR3oy/HTVsVbDvLVkZ7"
"BZZ4+M4UhcNARooYg3RZcdZymasHbVW5GBGvpGetW8pUmVniCYV2R9UZjWmdGpPO"
"2O/2UrkNpOuiceeFEvAZqOsodWc28yo5VhsIlAUPqkJOh5XnpGUP2p49VVhKlm6X"
"mQsaRcius1urXT3gp3W/7TtHpiJ8XD06L5i8hdBXybMZrO8uGfEkUH5Nc8HCqNA4"
"POiCTq/N/P0NkYrGEpgMeH4oHTVhYq5eh+8MaopmsLiZgC3tNkZri0wI3DBL8Xrl"
"rwIDAQAB"
"-----END PUBLIC KEY-----"


class AzureADTestCase(SecurityMonkeyTestCase):
    def test_azure_post(self):
        aad = AzureAD()
        (test_secret, test_algo) = aad.get_idp_cert(encoded_id_token, TEST_CONFIG['jwksUrl'])
        self.assertEqual(secret, test_secret)
        test_username = aad.validate_id_token(encoded_id_token, TEST_CONFIG['clientID'],TEST_CONFIG['jwksUrl'])
        self.assertEqual(test_username, decoded_id_token['email'])



