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
.. module: security_monkey.watchers.iam.iam_ssl
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey import app, AWS_DEFAULT_REGION

from cryptography import x509
from cryptography.hazmat.backends import default_backend


def cert_get_signing_algorithm(cert):
    return cert.signature_hash_algorithm.name


def cert_get_bitstrength(cert):
    """
    Calculates a certificates public key bit length.

    :param cert:
    :return: Integer
    """
    if hasattr(cert.public_key(), 'key_size'):
        return cert.public_key().key_size
    else:
        return None


def cert_get_issuer(cert):
    """
    Gets a sane issuer from a given certificate.

    :param cert:
    :return: Issuer
    """
    delchars = ''.join(c for c in map(chr, list(range(256))) if not c.isalnum())
    try:
        issuer = str(cert.issuer.get_attributes_for_oid(x509.OID_ORGANIZATION_NAME)[0].value)
        for c in delchars:
            issuer = issuer.replace(c, "")
        return issuer
    except Exception as e:
        app.logger.error("Unable to get issuer! {0}".format(e))
        return 'ERROR_EXTRACTING_ISSUER'



def cert_get_serial(cert):
    """
    Fetch serial number from the certificate

    :param cert:
    :return:
    """
    return cert.serial_number


def cert_get_not_before(cert):
    """
    Gets the naive datetime of the certificates 'not_before' field.
    This field denotes the first date in time which the given certificate
    is valid.

    :param cert:
    :return:
    """
    return cert.not_valid_before


def cert_get_not_after(cert):
    """
    Gets the naive datetime of the certificates 'not_after' field.
    This field denotes the last date in time which the given certificate
    is valid.

    :param cert:
    :return:
    """
    return cert.not_valid_after


def cert_get_domains(cert):
    """
    Attempts to get an domains listed in a certificate.
    If 'subjectAltName' extension is not available we simply
    return the common name.

    :param cert:
    :return: List of domains
    """
    domains = []
    try:
        ext = cert.extensions.get_extension_for_oid(x509.OID_SUBJECT_ALTERNATIVE_NAME)
        entries = ext.value.get_values_for_type(x509.DNSName)
        for entry in entries:
            domains.append(entry)
    except Exception as e:
        if app.config.get("LOG_SSL_SUBJ_ALT_NAME_ERRORS", True):
            app.logger.warning("Failed to get SubjectAltName: {0}".format(e), exc_info=True)

    return domains


def cert_get_cn(cert):
    """
    Attempts to get a sane common name from a given certificate.

    :param cert:
    :return: Common name or None
    """
    cn = cert.subject.get_attributes_for_oid(x509.OID_COMMON_NAME)
    if len(cn) > 0:
        return cn[0].value.strip()
    return ''


def cert_is_san(cert):
    """
    Determines if a given certificate is a SAN certificate.
    SAN certificates are simply certificates that cover multiple domains.

    :param cert:
    :return: Bool
    """
    if len(cert_get_domains(cert)) > 1:
        return True


def cert_is_wildcard(cert):
    """
    Determines if certificate is a wildcard certificate.

    :param cert:
    :return: Bool
    """
    domains = cert_get_domains(cert)
    if len(domains) == 1 and domains[0][0:1] == "*":
        return True

    cn = cert.subject.get_attributes_for_oid(x509.OID_COMMON_NAME)
    if len(cn) > 0 and cn[0].value[0:1] == "*":
        return True


def get_cert_info(body):
    cert = x509.load_pem_x509_certificate((body), default_backend())
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
                # Purposely sending default region instead of universal.
                all_certs = self.get_all_certs_in_region(account, AWS_DEFAULT_REGION, exception_map)
                for cert in all_certs:
                    name = cert['server_certificate_name']
                    # Purposely saving as 'universal'.
                    item = IAMSSLItem(account=account, name=name, arn=cert.get('arn'), region=region, config=dict(cert),
                                      source_watcher=self)
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
                if certs.is_truncated == 'true':
                    marker = certs.marker
                else:
                    break

            for cert in all_certs:
                try:
                    iam_cert = self.wrap_aws_rate_limited_call(
                        iamconn.get_server_certificate,
                        cert_name=cert.server_certificate_name
                    )
                    cert['body'] = iam_cert.certificate_body
                    cert['chain'] = None
                    if hasattr(iam_cert, 'certificate_chain'):
                        cert['chain'] = iam_cert.certificate_chain

                    cert_info = get_cert_info(cert['body'])
                    for key in cert_info.keys():
                        cert[key] = cert_info[key]

                except Exception as e:
                    app.logger.warn(traceback.format_exc())
                    app.logger.error("Invalid certificate {}!".format(cert.server_certificate_id))
                    self.slurp_exception(
                        (self.index, account, 'universal', cert.server_certificate_name),
                        e, exception_map, source="{}-watcher".format(self.index))

        except Exception as e:
            app.logger.warn(traceback.format_exc())
            if region not in TROUBLE_REGIONS:
                exc = BotoConnectionIssue(str(e), self.index, account, 'universal')
                self.slurp_exception((self.index, account, 'universal'), exc, exception_map,
                                     source="{}-watcher".format(self.index))
        app.logger.info("Found {} {} from {}/{}".format(len(all_certs), self.i_am_plural, account, 'universal'))
        return all_certs


class IAMSSLItem(ChangeItem):
    def __init__(self, account=None, name=None, arn=None, region=None, config=None, source_watcher=None):
        super(IAMSSLItem, self).__init__(
            index=IAMSSL.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config if config else {},
            source_watcher=source_watcher)
