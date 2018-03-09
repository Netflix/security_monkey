#     Copyright 2016 Bridgewater Associates
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
.. module: security_monkey.watchers.vpc.networkacl
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.decorators import record_exception, iter_account_region
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey import app


class NetworkACL(Watcher):
    index = 'networkacl'
    i_am_singular = 'Network ACL'
    i_am_plural = 'Network ACLs'

    def __init__(self, accounts=None, debug=False):
        super(NetworkACL, self).__init__(accounts=accounts, debug=debug)

    @record_exception()
    def describe_network_acls(self, **kwargs):
        from security_monkey.common.sts_connect import connect
        conn = connect(kwargs['account_name'], 'boto3.ec2.client', region=kwargs['region'],
                       assumed_role=kwargs['assumed_role'])

        networkacls_resp = self.wrap_aws_rate_limited_call(
            conn.describe_network_acls)
        networkacls = networkacls_resp.get('NetworkAcls', [])
        return networkacls

    def slurp(self):
        """
        :returns: item_list - list of network acls.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()

        @iter_account_region(index=self.index, accounts=self.accounts, service_name='ec2')
        def slurp_items(**kwargs):
            item_list = []
            exception_map = {}
            kwargs['exception_map'] = exception_map
            app.logger.debug("Checking {}/{}/{}".format(self.index,
                                                        kwargs['account_name'], kwargs['region']))
            networkacls = self.describe_network_acls(**kwargs)

            if networkacls:
                for nacl in networkacls:

                    nacl_id = nacl.get('NetworkAclId')

                    if self.check_ignore_list(nacl_id):
                        continue

                    config = {
                        'id': nacl_id,
                        'vpc_id': nacl.get('VpcId'),
                        'is_default': bool(nacl.get('IsDefault')),
                        'entries': nacl.get('Entries'),
                        'associations': nacl.get('Associations'),
                        'tags': nacl.get('Tags')
                    }

                    item = NetworkACLItem(region=kwargs['region'],
                                          account=kwargs['account_name'],
                                          name=nacl_id, config=config, source_watcher=self)

                    item_list.append(item)

            return item_list, exception_map
        return slurp_items()


class NetworkACLItem(ChangeItem):

    def __init__(self, region=None, account=None, name=None, config=None, source_watcher=None):
        super(NetworkACLItem, self).__init__(
            index=NetworkACL.index,
            region=region,
            account=account,
            name=name,
            new_config=config if config else {},
            source_watcher=source_watcher)
