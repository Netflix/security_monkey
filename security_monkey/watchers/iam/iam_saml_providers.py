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
.. module: security_monkey.watchers.iam.saml_provider
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: William Bengtson <wbengtson@netlfix.com> @willbengtson

"""

from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey import app

import defusedxml.ElementTree as ET


class SamlProvider(Watcher):
    index = 'samlprovider'
    saml_singular = 'SAML Provider'
    saml_plural = 'SAML Providers'

    def __init__(self, accounts=None, debug=False):
        super(SamlProvider, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        """
        :returns: item_list - list of SAML Providers.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception
        """
        self.prep_for_slurp()
        item_list = []
        exception_map = {}

        from security_monkey.common.sts_connect import connect
        for account in self.accounts:
            all_saml_providers = []

            try:
                iam = connect(account, 'boto3.iam.client')

                providers = iam.list_saml_providers()

                for provider in providers.get('SAMLProviderList',[]):
                    all_saml_providers.append(provider)

            except Exception as e:
                exc = BotoConnectionIssue(str(e), 'iamuser', account, None)
                self.slurp_exception((self.index, account, 'universal'), exc, exception_map,
                                     source="{}-watcher".format(self.index))
                continue

            for provider in all_saml_providers:

                if self.check_ignore_list(provider['Arn']):
                    continue

                # Get the SAML Provider information
                saml_provider = iam.get_saml_provider(SAMLProviderArn=provider['Arn'])

                # Parse the SAML Metadata XML Document
                root = ET.fromstring(saml_provider['SAMLMetadataDocument'])

                saml_x509 = ''
                company = ''
                given_name = ''
                email_address = ''

                for parent in root.getiterator():
                    for child in parent:
                        if 'X509Certificate' in child.tag:
                            saml_x509 = child.text
                        if 'Company' in child.tag:
                            company = child.text
                        if 'GivenName' in child.tag:
                            given_name = child.text
                        if 'EmailAddress' in child.tag:
                            email_address = child.text


                item_config = {
                    'name': root.attrib['entityID'],
                    'arn': provider['Arn'],
                    'create_date': str(saml_provider['CreateDate']),
                    'valid_until': str(saml_provider['ValidUntil']),
                    'x509': saml_x509,
                    'company': company,
                    'given_name': given_name,
                    'email': email_address
                }

                app.logger.debug("Slurping %s (%s) from %s" % (self.saml_singular, root.attrib['entityID'], account))

                item_list.append(
                    SamlProviderItem(account=account, name=root.attrib['entityID'], arn=provider['Arn'], config=item_config)
                )

        return item_list, exception_map


class SamlProviderItem(ChangeItem):
    def __init__(self, account=None, name=None, arn=None, config={}):
        super(SamlProviderItem, self).__init__(
            index=SamlProvider.index,
            region='universal',
            account=account,
            name=name,
            arn=arn,
            new_config=config)
