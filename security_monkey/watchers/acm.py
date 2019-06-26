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
.. module: security_monkey.watchers.acm
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Alex Cline <alex.cline@gmail.com> @alex.cline

"""

from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey import app

from dateutil.tz import tzutc


class ACM(Watcher):
    index = 'acm'
    i_am_singular = 'ACM Certificate'
    i_am_plural = 'ACM Certificates'

    def describe_certificate(self, acm, arn):
        details = self.wrap_aws_rate_limited_call(
            acm.describe_certificate,
            CertificateArn=arn
        )
        return details

    def __init__(self, accounts=None, debug=False):
        super(ACM, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        """
        :returns: item_list - list of ACM Certificates with details.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()

        item_list = []
        exception_map = {}
        from security_monkey.common.sts_connect import connect
        for account in self.accounts:
            try:
                ec2 = connect(account, 'ec2')
                regions = ec2.get_all_regions()
            except Exception as e:  # EC2ResponseError
                # Some Accounts don't subscribe to EC2 and will throw an exception here.
                exc = BotoConnectionIssue(str(e), 'keypair', account, None)
                self.slurp_exception((self.index, account), exc, exception_map,
                                     source="{}-watcher".format(self.index))
                continue

            for region in regions:
                app.logger.debug("Checking {}/{}/{}".format(ACM.index, account, region.name))
                try:
                    acm = connect(account, 'boto3.acm.client', region=region, debug=1000)
                    response = self.wrap_aws_rate_limited_call(
                        acm.list_certificates
                    )
                    cert_list = response.get('CertificateSummaryList')
                except Exception as e:
                    if region.name not in TROUBLE_REGIONS:
                        exc = BotoConnectionIssue(str(e), 'acm', account, region.name)
                        self.slurp_exception((self.index, account, region.name), exc, exception_map,
                                             source="{}-watcher".format(self.index))
                    continue
                app.logger.debug("Found {} {}".format(len(cert_list), ACM.i_am_plural))

                for cert in cert_list:
                    app.logger.debug("Getting {} details for {}".format(ACM.i_am_singular, cert.get('DomainName')))
                    try:
                        config = self.describe_certificate(acm, cert.get('CertificateArn')).get('Certificate')

                        # Convert the datetime objects into ISO formatted strings in UTC
                        if config.get('NotBefore'):
                            config.update({ 'NotBefore': config.get('NotBefore').astimezone(tzutc()).isoformat() })
                        if config.get('NotAfter'):
                            config.update({ 'NotAfter': config.get('NotAfter').astimezone(tzutc()).isoformat() })
                        if config.get('CreatedAt'):
                            config.update({ 'CreatedAt': config.get('CreatedAt').astimezone(tzutc()).isoformat() })
                        if config.get('IssuedAt'):
                            config.update({ 'IssuedAt': config.get('IssuedAt').astimezone(tzutc()).isoformat() })
                        if config.get('ImportedAt'):
                            config.update({ 'ImportedAt': config.get('ImportedAt').astimezone(tzutc()).isoformat()})
                        if config.get('RenewalSummary', {}).get('UpdatedAt'):
                            config['RenewalSummary']['UpdatedAt'] = config['RenewalSummary']['UpdatedAt'].astimezone(
                                tzutc()).isoformat()

                        item = ACMCertificate(region=region.name, account=account, name=cert.get('DomainName'),
                                              arn=cert.get('CertificateArn'), config=dict(config), source_watcher=self)
                        item_list.append(item)
                    except Exception as e:
                        exc = BotoConnectionIssue(str(e), 'acm', account, region.name)
                        self.slurp_exception((self.index, account, region.name), exc, exception_map,
                                             source="{}-watcher".format(self.index))

        return item_list, exception_map


class ACMCertificate(ChangeItem):
    def __init__(self, region=None, account=None, name=None, arn=None, config=None, source_watcher=None):
        super(ACMCertificate, self).__init__(
            index=ACM.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config if config else {},
            source_watcher=source_watcher)
