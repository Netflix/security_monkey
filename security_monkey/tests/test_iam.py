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
from security_monkey.tests import SecurityMonkeyTestCase

from cryptography import x509
from cryptography.hazmat.backends import default_backend

INTERNAL_VALID_LONG_STR = b"""
-----BEGIN CERTIFICATE-----
MIID1zCCAr+gAwIBAgIBATANBgkqhkiG9w0BAQsFADCBjDELMAkGA1UEBhMCVVMx
CzAJBgNVBAgMAkNBMRAwDgYDVQQHDAdBIHBsYWNlMRcwFQYDVQQDDA5sb25nLmxp
dmVkLmNvbTEQMA4GA1UECgwHRXhhbXBsZTETMBEGA1UECwwKT3BlcmF0aW9uczEe
MBwGCSqGSIb3DQEJARYPamltQGV4YW1wbGUuY29tMB4XDTE1MDYyNjIwMzA1MloX
DTQwMDEwMTIwMzA1MlowgYwxCzAJBgNVBAYTAlVTMQswCQYDVQQIDAJDQTEQMA4G
A1UEBwwHQSBwbGFjZTEXMBUGA1UEAwwObG9uZy5saXZlZC5jb20xEDAOBgNVBAoM
B0V4YW1wbGUxEzARBgNVBAsMCk9wZXJhdGlvbnMxHjAcBgkqhkiG9w0BCQEWD2pp
bUBleGFtcGxlLmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKeg
sqb0HI10i2eRSx3pLeA7JoGdUpud7hy3bGws/1HgOSpRMin9Y65DEpVq2Ia9oir7
XOJLpSTEIulnBkgDHNOsdKVYHDR6k0gUisnIKSl2C3IgKHpCouwiOvvVPwd3PExg
17+d7KLBIu8LpG28wkXKFU8vSz5i7H4i/XCEChnKJ4oGJuGAJJM4Zn022U156pco
97aEAc9ZXR/1dm2njr4XxCXmrnKCYTElfRhLkmxtv+mCi6eV//5d12z7mY3dTBkQ
EG2xpb5DQ+ITQ8BzsKcPX80rz8rTzgYFwaV3gUg38+bgka/JGJq8HgBuNnHv5CeT
1T/EoZTRYW2oPfOgQK8CAwEAAaNCMEAwDwYDVR0TAQH/BAUwAwEB/zAOBgNVHQ8B
Af8EBAMCAQYwHQYDVR0OBBYEFIuDY73dQIhj2nnd4DG2SvseHVVaMA0GCSqGSIb3
DQEBCwUAA4IBAQBk/WwfoWYdS0M8rz5tJda/cMdYFSugUbTn6JJdmHuw6RmiKzKG
8NzfSqBR6m8MWdSTuAZ/chsUZH9YEIjS9tAH9/FfUFBrsUE7TXaUgpNBm4DBLLfl
fj5xDmEyj17JPN/C36amQ9eU5BNesdCx9EkdWLyVJaM50HFRo71W0/FrpKZyKK68
XPhd1z9w/xgfCfYhe7PjEmrmNPN5Tgk5TyXW+UUhOepDctAv2DBetptcx+gHrtW+
Ygk1wptlt/tg7uUmstmXZA4vTPx83f4P3KSS3XHIYFIyGFWUDs23C20K6mmW1iXa
h0S8LN4iv/+vNFPNiM1z9X/SZgfbwZXrLsSi
-----END CERTIFICATE-----
"""
INTERNAL_VALID_LONG_CERT = x509.load_pem_x509_certificate(INTERNAL_VALID_LONG_STR, default_backend())


INTERNAL_INVALID_STR = b"""
-----BEGIN CERTIFICATE-----
MIIEFTCCAv2gAwIBAgICA+gwDQYJKoZIhvcNAQELBQAwgYwxCzAJBgNVBAYTAlVT
MQswCQYDVQQIDAJDQTEQMA4GA1UEBwwHQSBwbGFjZTEXMBUGA1UEAwwObG9uZy5s
aXZlZC5jb20xEDAOBgNVBAoMB0V4YW1wbGUxEzARBgNVBAsMCk9wZXJhdGlvbnMx
HjAcBgkqhkiG9w0BCQEWD2ppbUBleGFtcGxlLmNvbTAeFw0xNTA2MjYyMDM2NDha
Fw0xNTA2MjcyMDM2NDhaMGkxCzAJBgNVBAYTAlVTMQswCQYDVQQIEwJDQTEQMA4G
A1UEBxMHQSBwbGFjZTEQMA4GA1UEChMHRXhhbXBsZTETMBEGA1UECxMKT3BlcmF0
aW9uczEUMBIGA1UEAxMLZXhwaXJlZC5jb20wggEiMA0GCSqGSIb3DQEBAQUAA4IB
DwAwggEKAoIBAQCcSMzRxB6+UONPqYMy1Ojw3Wi8DIpt9USnSR60I8LiEuRK2ayr
0RMjLJ6sBEgy/hISEqpLgTsciDpxwaTC/WNrkT9vaMcwfiG3V0Red8zbKHQzC+Ty
cLRg9wbC3v613kaIZCQCoE7Aouru9WbVPmuRoasfztrgksWmH9infQbL4TDcmcxo
qGaMn4ajQTVAD63CKnut+CULZIMBREBVlSTLiOO7qZdTrd+vjtLWvdXVPcWLSBrd
Vpu3YnhqqTte+DMzQHwY7A2s3fu4Cg4H4npzcR+0H1H/B5z64kxqZq9FWGIcZcz7
0xXeHN9UUKPDSTgsjtIzKTaIOe9eML3jGSU7AgMBAAGjgaIwgZ8wDAYDVR0TAQH/
BAIwADAOBgNVHQ8BAf8EBAMCBaAwFgYDVR0lAQH/BAwwCgYIKwYBBQUHAwEwHQYD
VR0OBBYEFKwBYaxCLxK0csmV319rbRdqDllWMEgGA1UdHwRBMD8wPaA7oDmGN2h0
dHA6Ly90ZXN0LmNsb3VkY2EuY3JsLm5ldGZsaXguY29tL2xvbmdsaXZlZENBL2Ny
bC5wZW0wDQYJKoZIhvcNAQELBQADggEBADFngqsMsGnNBWknphLDvnoWu5MTrpsD
AgN0bktv5ACKRWhi/qtCmkEf6TieecRMwpQNMpE50dko3LGGdWlZRCI8wdH/zrw2
8MnOeCBxuS1nB4muUGjbf4LIbtuwoHSESrkfmuKjGGK9JTszLL6Hb9YnoFefeg8L
T7W3s8mm5bVHhQM7J9tV6dz/sVDmpOSuzL8oZkqeKP+lWU6ytaohFFpbdzaxWipU
3+GobVe4vRqoF1kwuhQ8YbMbXWDK6zlrT9pjFABcQ/b5nveiW93JDQUbjmVccx/u
kP+oGWtHvhteUAe8Gloo5NchZJ0/BqlYRCD5aAHcmbXRsDid9mO4ADU=
-----END CERTIFICATE-----
"""
INTERNAL_INVALID_CERT = x509.load_pem_x509_certificate(INTERNAL_INVALID_STR, default_backend())


INTERNAL_VALID_SAN_STR = b"""
-----BEGIN CERTIFICATE-----
MIIESjCCAzKgAwIBAgICA+kwDQYJKoZIhvcNAQELBQAwgYwxCzAJBgNVBAYTAlVT
MQswCQYDVQQIDAJDQTEQMA4GA1UEBwwHQSBwbGFjZTEXMBUGA1UEAwwObG9uZy5s
aXZlZC5jb20xEDAOBgNVBAoMB0V4YW1wbGUxEzARBgNVBAsMCk9wZXJhdGlvbnMx
HjAcBgkqhkiG9w0BCQEWD2ppbUBleGFtcGxlLmNvbTAeFw0xNTA2MjYyMDU5MDZa
Fw0yMDAxMDEyMDU5MDZaMG0xCzAJBgNVBAYTAlVTMQswCQYDVQQIEwJDQTEQMA4G
A1UEBxMHQSBwbGFjZTEQMA4GA1UEChMHRXhhbXBsZTETMBEGA1UECxMKT3BlcmF0
aW9uczEYMBYGA1UEAxMPc2FuLmV4YW1wbGUuY29tMIIBIjANBgkqhkiG9w0BAQEF
AAOCAQ8AMIIBCgKCAQEA2Nq5zFh2WiqtNIPssdSwQ9/00j370VcKPlOATLqK24Q+
dr2hWP1WlZJ0NOoPefhoIysccs2tRivosTpViRAzNJXigBHhxe8ger0QhVW6AXIp
ov327N689TgY4GzRrwqavjz8cqussIcnEUr4NLLsU5AvXE7e3WxYkkskzO497UOI
uCBtWdCXZ4cAGhtVkkA5uQHfPsLmgRVoUmdMDt5ZmA8HhLX4X6vkT3oGIhdGCw6T
W+Cu7PfYlSaggSBbBniU0YKTFLfGLkYFZN/b6bxzvt6CTJLoVFAYXyLJwUvd3EAm
u23HgUflIyZNG3xVPml/lah0OIX7RtSigXUSLm7lYwIDAQABo4HTMIHQMAwGA1Ud
EwEB/wQCMAAwDgYDVR0PAQH/BAQDAgWgMBYGA1UdJQEB/wQMMAoGCCsGAQUFBwMB
MC8GA1UdEQQoMCaCEWV4YW1wbGUyLmxvbmcuY29tghFleGFtcGxlMy5sb25nLmNv
bTAdBgNVHQ4EFgQUiiIyclcBIfJ5PE3OCcTXwzJAM+0wSAYDVR0fBEEwPzA9oDug
OYY3aHR0cDovL3Rlc3QuY2xvdWRjYS5jcmwubmV0ZmxpeC5jb20vbG9uZ2xpdmVk
Q0EvY3JsLnBlbTANBgkqhkiG9w0BAQsFAAOCAQEAgcTioq70B/aPWovNTy+84wLw
VX1q6bCdH3FJwAv2rc28CHp5mCGdR6JqfT/H/CbfRwT1Yh/5i7T5kEVyz+Dp3+p+
AJ2xauHrTvWn0QHQYbUWICwkuZ7VTI9nd0Fry1FQI1EeKiCmyrzNljiN2l+GZw6i
NJUpVNtwRyWRzB+yIx2E9wyydqDFH+sROuQok7EgzlQileitPrF4RrkfIhQp2/ki
YBrY/duF15YpoMKAlFhDBh6R9/nb5kI2n3pY6I5h6LEYfLStazXbIu61M8zu9TM/
+t5Oz6rmcjohL22+sEmmRz86dQZlrBBUxX0kCQj6OAFB4awtRd4fKtkCkZhvhQ==
-----END CERTIFICATE-----
"""
INTERNAL_VALID_SAN_CERT = x509.load_pem_x509_certificate(INTERNAL_VALID_SAN_STR, default_backend())


INTERNAL_VALID_WILDCARD_STR = b"""
-----BEGIN CERTIFICATE-----
MIIEHDCCAwSgAwIBAgICA+owDQYJKoZIhvcNAQELBQAwgYwxCzAJBgNVBAYTAlVT
MQswCQYDVQQIDAJDQTEQMA4GA1UEBwwHQSBwbGFjZTEXMBUGA1UEAwwObG9uZy5s
aXZlZC5jb20xEDAOBgNVBAoMB0V4YW1wbGUxEzARBgNVBAsMCk9wZXJhdGlvbnMx
HjAcBgkqhkiG9w0BCQEWD2ppbUBleGFtcGxlLmNvbTAeFw0xNTA2MjYyMTEzMTBa
Fw0yMDAxMDEyMTEzMTBaMHAxCzAJBgNVBAYTAlVTMQswCQYDVQQIEwJDQTEQMA4G
A1UEBxMHQSBwbGFjZTEQMA4GA1UEChMHRXhhbXBsZTETMBEGA1UECxMKT3BlcmF0
aW9uczEbMBkGA1UEAxQSKi50ZXN0LmV4YW1wbGUuY29tMIIBIjANBgkqhkiG9w0B
AQEFAAOCAQ8AMIIBCgKCAQEA0T7OEY9FxMIdhe1CwLc+TbDeSfDN6KRHlp0I9MwK
3Pre7A1+1vmRzLiS5qAdOh3Oexelmgdkn/fZUFI+IqEVJwmeUiq13Kib3BFnVtbB
N1RdT7rZF24Bqwygf1DHAekEBYdvu4dGD/gYKsLYsSMD7g6glUuhTbgR871updcV
USYJ801y640CcHjai8UCLxpqtkP/Alob+/KDczUHbhdxYgmH34aQgxC8zg+uzuq6
bIqUAc6SctI+6ArXOqri7wSMgZUnogpF4R5QbCnlDfSzNcNxJFtGp8cy7CNWebMd
IWgBYwee8i8S6Q90B2QUFD9EGG2pEZldpudTxWUpq0tWmwIDAQABo4GiMIGfMAwG
A1UdEwEB/wQCMAAwDgYDVR0PAQH/BAQDAgWgMBYGA1UdJQEB/wQMMAoGCCsGAQUF
BwMBMB0GA1UdDgQWBBTH2KIECrqPHMbsVysGv7ggkYYZGDBIBgNVHR8EQTA/MD2g
O6A5hjdodHRwOi8vdGVzdC5jbG91ZGNhLmNybC5uZXRmbGl4LmNvbS9sb25nbGl2
ZWRDQS9jcmwucGVtMA0GCSqGSIb3DQEBCwUAA4IBAQBjjfur2B6BcdIQIouwhXGk
IFE5gUYMK5S8Crf/lpMxwHdWK8QM1BpJu9gIo6VoM8uFVa8qlY8LN0SyNyWw+qU5
Jc8X/qCeeJwXEyXY3dIYRT/1aj7FCc7EFn1j6pcHPD6/0M2z0Zmj+1rWNBJdcYor
pCy27OgRoJKZ6YhEYekzwIPeFPL6irIN9xKPnfH0b2cnYa/g56DyGmyKH2Kkhz0A
UGniiUh4bAUuppbtSIvUTsRsJuPYOqHC3h8791JZ/3Sr5uB7QbCdz9K14c9zi6Z1
S0Xb3ZauZJQI7OdHeUPDRVq+8hcG77sopN9pEYrIH08oxvLX2US3GqrowjOxthRa
-----END CERTIFICATE-----
"""
INTERNAL_VALID_WILDCARD_CERT = x509.load_pem_x509_certificate(INTERNAL_VALID_WILDCARD_STR, default_backend())


EXTERNAL_VALID_STR = b"""
-----BEGIN CERTIFICATE-----
MIIFHzCCBAegAwIBAgIQGFWCciDWzbOej/TbAJN0WzANBgkqhkiG9w0BAQsFADCB
pDELMAkGA1UEBhMCVVMxHTAbBgNVBAoTFFN5bWFudGVjIENvcnBvcmF0aW9uMR8w
HQYDVQQLExZGT1IgVEVTVCBQVVJQT1NFUyBPTkxZMR8wHQYDVQQLExZTeW1hbnRl
YyBUcnVzdCBOZXR3b3JrMTQwMgYDVQQDEytTeW1hbnRlYyBDbGFzcyAzIFNlY3Vy
ZSBTZXJ2ZXIgVEVTVCBDQSAtIEc0MB4XDTE1MDYyNDAwMDAwMFoXDTE1MDYyNTIz
NTk1OVowgYMxCzAJBgNVBAYTAlVTMRMwEQYDVQQIDApDQUxJRk9STklBMRIwEAYD
VQQHDAlMb3MgR2F0b3MxFjAUBgNVBAoMDU5ldGZsaXgsIEluYy4xEzARBgNVBAsM
Ck9wZXJhdGlvbnMxHjAcBgNVBAMMFXR0dHQyLm5ldGZsaXh0ZXN0Lm5ldDCCASIw
DQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALwMY/yod9YGLKLCzbbsSUBWm4ZC
DfcgbUNL3JLtZaFCaOeUPLa4YNqty+9ACXBLYPNMm+dgsRHix8N2uwtZrGazHILK
qey96eSTosPsvKFt0KLNpUl8GC/YxA69L128SJgFaaq5Dr2Mp3NP0rt0RIz5luPj
Oae0hkGOS8uS0dySlAmfOw2OsJY3gCw5UHcmpcCHpO2f7uU+tWKmgfz4U/PpQ0kz
WVJno+JhcaXIximtiLreCNF1LpraAjrcZJ+ySJwYaLaYMiJoFkdXUtKJcyqmkbA3
Splt7N4Hb8c+5aXv225uQYCh0HXQeMyBotlaIrAddP5obrtjxhXBxB4ysEcCAwEA
AaOCAWowggFmMCAGA1UdEQQZMBeCFXR0dHQyLm5ldGZsaXh0ZXN0Lm5ldDAJBgNV
HRMEAjAAMA4GA1UdDwEB/wQEAwIFoDAdBgNVHSUEFjAUBggrBgEFBQcDAQYIKwYB
BQUHAwIwYQYDVR0gBFowWDBWBgZngQwBAgIwTDAjBggrBgEFBQcCARYXaHR0cHM6
Ly9kLnN5bWNiLmNvbS9jcHMwJQYIKwYBBQUHAgIwGRoXaHR0cHM6Ly9kLnN5bWNi
LmNvbS9ycGEwHwYDVR0jBBgwFoAUNI9UtT8KH1K6nLJl7bqLCGcZ4AQwKwYDVR0f
BCQwIjAgoB6gHIYaaHR0cDovL3NzLnN5bWNiLmNvbS9zcy5jcmwwVwYIKwYBBQUH
AQEESzBJMB8GCCsGAQUFBzABhhNodHRwOi8vc3Muc3ltY2QuY29tMCYGCCsGAQUF
BzAChhpodHRwOi8vc3Muc3ltY2IuY29tL3NzLmNydDANBgkqhkiG9w0BAQsFAAOC
AQEAQuIfyBltvCZ9orqNdS6PUo2PaeUgJzkmdDwbDVd7rTwbZIwGZXZjeKseqMSb
L+r/jN6DWrScVylleiz0N/D0lSUhC609dQKuicGpy3yQaXwhfYZ6duxrW3Ii/+Vz
pFv7DnG3JPZjIXCmVhQVIv/8oaV0bfUF/1mrWRFwZiBILxa7iaycRhjusJEVRtzN
Ot/qkLluHO0wbEHnASV4P9Y5NuR/bliuFS/DeRczofNS78jJuZrGvl2AqS/19Hvm
Bs63gULVCqWygt5KEbv990m/XGuRMaXuHzHCHB4v5LRM30FiFmqCzyD8d+btzW9B
1hZ5s3rj+a6UwvpinKJoPfgkgg==
-----END CERTIFICATE-----
"""
EXTERNAL_CERT = x509.load_pem_x509_certificate(EXTERNAL_VALID_STR, default_backend())

FULL_ADMIN_POLICY_BARE="""
{
    "Statement":    {
        "Effect": "Allow",
        "Action": "*"
    }
}
"""

FULL_ADMIN_POLICY_SINGLE_ENTRY="""
{
    "Statement":    {
        "Effect": "Allow",
        "Action": ["*"]
    }
}
"""

FULL_ADMIN_POLICY_LIST="""
{
    "Statement":    {
        "Effect": "Allow",
        "Action": [
            "filler",
            "*",
            "morefiller"
        ]
    }
}
"""

NO_ADMIN_POLICY_LIST="""
{
    "Statement":    {
        "Effect": "Allow",
        "Action": [
            "filler",
            "morefiller"
        ]
    }
}
"""



class MockIAMObj:
    def __init__(self):
        self.config = {}
        self.audit_issues = []
        self.index = "unittestindex"
        self.region = "unittestregion"
        self.account = "unittestaccount"
        self.name = "unittestname"


class IAMTestCase(SecurityMonkeyTestCase):
    def test_cert_get_cn(self):
        from security_monkey.watchers.iam.iam_ssl import cert_get_cn
        self.assertEqual(cert_get_cn(INTERNAL_VALID_LONG_CERT), 'long.lived.com')

    def test_cert_get_subAltDomains(self):
        from security_monkey.watchers.iam.iam_ssl import cert_get_domains

        self.assertEqual(cert_get_domains(INTERNAL_VALID_LONG_CERT), [])
        self.assertEqual(cert_get_domains(INTERNAL_VALID_SAN_CERT), ['example2.long.com', 'example3.long.com'])

    def test_cert_is_san(self):
        from security_monkey.watchers.iam.iam_ssl import cert_is_san

        self.assertIsNone(cert_is_san(INTERNAL_VALID_LONG_CERT))
        self.assertTrue(cert_is_san(INTERNAL_VALID_SAN_CERT))

    def test_cert_is_wildcard(self):
        from security_monkey.watchers.iam.iam_ssl import cert_is_wildcard
        self.assertTrue(cert_is_wildcard(INTERNAL_VALID_WILDCARD_CERT))
        self.assertIsNone(cert_is_wildcard(INTERNAL_VALID_LONG_CERT))

    def test_cert_get_bitstrength(self):
        from security_monkey.watchers.iam.iam_ssl import cert_get_bitstrength
        self.assertEqual(cert_get_bitstrength(INTERNAL_VALID_LONG_CERT), 2048)

    def test_cert_get_issuer(self):
        from security_monkey.watchers.iam.iam_ssl import cert_get_issuer
        self.assertEqual(cert_get_issuer(INTERNAL_VALID_LONG_CERT), 'Example')

    def test_get_cert_info(self):
        from security_monkey.watchers.iam.iam_ssl import get_cert_info
        valid = {
            'cn': u'tttt2.netflixtest.net',
            'domains': [u'tttt2.netflixtest.net'],
            'is_san': None,
            'is_wildcard': None,
            'issuer': 'SymantecCorporation',
            'not_valid_after': '2015-06-25 23:59:59',
            'not_valid_before': '2015-06-24 00:00:00',
            'serial': '32345462887235644479608430756355077211',
            'signature_algorithm': 'sha256',
            'size': 2048
        }

        self.assertEqual(get_cert_info(EXTERNAL_VALID_STR), valid)

    def test_iam_full_admin_only(self):
        import json
        from security_monkey.auditors.iam.iam_policy import IAMPolicyAuditor

        auditor = IAMPolicyAuditor( accounts=['unittest'])
        iamobj = MockIAMObj()

        iamobj.config = {'userpolicies': json.loads(FULL_ADMIN_POLICY_BARE)}

        self.assertIs(len(iamobj.audit_issues), 0, "Policy should have 0 alert but has {}".format(len(iamobj.audit_issues)))
        auditor.library_check_iamobj_has_star_privileges(iamobj, multiple_policies=False)
        self.assertIs(len(iamobj.audit_issues), 1, "Policy should have 1 alert but has {}".format(len(iamobj.audit_issues)))

    def test_iam_full_admin_list_single_entry(self):
        import json
        from security_monkey.auditors.iam.iam_policy import IAMPolicyAuditor

        auditor = IAMPolicyAuditor( accounts=['unittest'])

        iamobj = MockIAMObj()
        iamobj.config = {'userpolicies': json.loads(FULL_ADMIN_POLICY_SINGLE_ENTRY)}

        self.assertIs(len(iamobj.audit_issues), 0, "Policy should have 0 alert but has {}".format(len(iamobj.audit_issues)))
        auditor.library_check_iamobj_has_star_privileges(iamobj, multiple_policies=False)
        self.assertIs(len(iamobj.audit_issues), 1, "Policy should have 1 alert but has {}".format(len(iamobj.audit_issues)))

    def test_iam_full_admin_list(self):
        import json
        from security_monkey.auditors.iam.iam_policy import IAMPolicyAuditor

        auditor = IAMPolicyAuditor( accounts=['unittest'])

        iamobj = MockIAMObj()
        iamobj.config = {'userpolicies': json.loads(FULL_ADMIN_POLICY_LIST)}

        self.assertIs(len(iamobj.audit_issues), 0, "Policy should have 0 alert but has {}".format(len(iamobj.audit_issues)))
        auditor.library_check_iamobj_has_star_privileges(iamobj, multiple_policies=False)
        self.assertIs(len(iamobj.audit_issues), 1, "Policy should have 1 alert but has {}".format(len(iamobj.audit_issues)))

    def test_iam_no_admin_list(self):
        import json
        from security_monkey.auditors.iam.iam_policy import IAMPolicyAuditor

        auditor = IAMPolicyAuditor( accounts=['unittest'])

        iamobj = MockIAMObj()
        iamobj.config = {'userpolicies': json.loads(NO_ADMIN_POLICY_LIST)}

        self.assertIs(len(iamobj.audit_issues), 0, "Policy should have 0 alert but has {}".format(len(iamobj.audit_issues)))
        auditor.library_check_iamobj_has_star_privileges(iamobj, multiple_policies=False)
        self.assertIs(len(iamobj.audit_issues), 0, "Policy should have 0 alert but has {}".format(len(iamobj.audit_issues)))
