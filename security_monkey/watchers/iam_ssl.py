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
                    cert_id = cert['server_certificate_id']
                    # Purposely saving as 'universal'.
                    item = IAMSSLItem(account=account, name=cert_id, region=region, config=dict(cert))
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
        except Exception as e:
            app.logger.warn(traceback.format_exc())
            if region not in TROUBLE_REGIONS:
                exc = BotoConnectionIssue(str(e), self.index, account, region)
                self.slurp_exception((self.index, account, region), exc, exception_map)
        app.logger.info("Found {} {} from {}/{}".format(len(all_certs), self.i_am_plural, account, region))
        return all_certs


class IAMSSLItem(ChangeItem):
    def __init__(self, account=None, name=None, region=None, config={}):
        super(IAMSSLItem, self).__init__(
            index=IAMSSL.index,
            region=region,
            account=account,
            name=name,
            new_config=config)
