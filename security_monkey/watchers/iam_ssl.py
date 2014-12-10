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
.. module: security_monkey.watchers.iam_ssl
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey import app

from M2Crypto import X509


def cert_get_signing_algorithm(cert):
    return cert.as_text().split("Signature Algorithm: ")[1].split("\n")[0]


def cert_get_bitstrength(cert):
    return cert.get_pubkey().size() * 8


def cert_get_issuer(cert):
    return str(cert.get_issuer()).split("/O=")[1].split("/")[0].translate(None, " ,.").strip()


def cert_get_serial(cert):
    return cert.get_serial_number()


def cert_get_not_before(cert):
    return cert.get_not_before().get_datetime().replace(tzinfo=None)


def cert_get_not_after(cert):
    return cert.get_not_after().get_datetime().replace(tzinfo=None)


def cert_get_cn(cert):
    return cert.get_subject().as_text().split("CN=")[1].strip().split(",")[0].strip().split("/")[0].strip()


def cert_is_san(cert):
    domains = cert_get_domains(cert)
    if len(domains) > 1:
        return True
    return False


def cert_get_domains(cert):
    domains = []
    try:
        ext = cert.get_ext("subjectAltName")
        entries = ext.get_value().split(",")
        for entry in entries:
            domains.append(entry.split(":")[1].strip(", "))
    except:
        domains.append(cert_get_cn(cert))
    return domains


def cert_is_wildcard(cert):
    domains = cert_get_domains(cert)
    if len(domains) == 1 and domains[0][0:1] == "*":
        return True
    return False


def get_cert_info(body):
    cert = X509.load_cert_string(str(body))
    cert_info = {
        'signature_algorithm': cert_get_signing_algorithm(cert),
        'size': cert_get_bitstrength(cert),
        'issuer': cert_get_issuer(cert),
        'serial': str(cert_get_serial(cert)),
        'cn': cert_get_cn(cert),
        'is_san': cert_is_san(cert),
        'is_wildcard': cert_is_wildcard(cert),
        'domains': cert_get_domains(cert),
        'not_valid_before': str(cert_get_not_before(cert)),
        'not_valid_after': str(cert_get_not_after(cert))
    }
    return cert_info


class IAMSSL(Watcher):
    index = 'iamssl'
    i_am_singular = 'IAM SSL'
    i_am_plural = 'IAM SSLs'

    def __init__(self, accounts=None, debug=False):
        super(IAMSSL, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        """
        :returns: item_list - list of IAM SSL Certificates.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception
        """
        item_list = []
        exception_map = {}
        for account in self.accounts:
            for region in ['universal']:
                # Purposely sending us-east-1 instead of universal.
                all_certs = self.get_all_certs_in_region(account, 'us-east-1', exception_map)
                for cert in all_certs:
                    name = cert['server_certificate_name']
                    # Purposely saving as 'universal'.
                    item = IAMSSLItem(account=account, name=name, region=region, config=dict(cert))
                    item_list.append(item)

        return item_list, exception_map

    def get_all_certs_in_region(self, account, region, exception_map):
        from security_monkey.common.sts_connect import connect
        import traceback
        all_certs = []
        app.logger.debug("Checking {}/{}/{}".format(self.index, account, region))
        try:
            iamconn = connect(account, 'iam', region=region)
            marker = None
            while True:
                certs = self.wrap_aws_rate_limited_call(
                    iamconn.list_server_certs,
                    marker=marker
                )
                all_certs.extend(certs.server_certificate_metadata_list)
                if certs.is_truncated == u'true':
                    marker = certs.marker
                else:
                    break

            for cert in all_certs:
                iam_cert = self.wrap_aws_rate_limited_call(
                    iamconn.get_server_certificate,
                    cert_name=cert.server_certificate_name
                )
                cert['body'] = iam_cert.certificate_body
                cert['chain'] = None
                if hasattr(iam_cert, 'certificate_chain'):
                    cert['chain'] = iam_cert.certificate_chain

                cert_info = get_cert_info(cert['body'])
                for key in cert_info.iterkeys():
                    cert[key] = cert_info[key]

        except Exception as e:
            app.logger.warn(traceback.format_exc())
            if region not in TROUBLE_REGIONS:
                exc = BotoConnectionIssue(str(e), self.index, account, 'universal')
                self.slurp_exception((self.index, account, 'universal'), exc, exception_map)
        app.logger.info("Found {} {} from {}/{}".format(len(all_certs), self.i_am_plural, account, 'universal'))
        return all_certs


class IAMSSLItem(ChangeItem):
    def __init__(self, account=None, name=None, region=None, config={}):
        super(IAMSSLItem, self).__init__(
            index=IAMSSL.index,
            region=region,
            account=account,
            name=name,
            new_config=config)
