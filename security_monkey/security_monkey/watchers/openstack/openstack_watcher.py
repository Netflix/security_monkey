#     Copyright (c) 2017 AT&T Intellectual Property. All rights reserved.
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
.. module: security_monkey.openstack.watchers.openstack_watcher
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Michael Stair <mstair@att.com>

"""

from security_monkey.cloudaux_watcher import CloudAuxWatcher, CloudAuxChangeItem
from security_monkey.decorators import record_exception

from cloudaux.openstack.decorators import iter_account_region, get_regions
from cloudaux.openstack.utils import list_items
from cloudaux.orchestration.openstack.utils import get_item


class OpenStackWatcher(CloudAuxWatcher):
    account_type = 'OpenStack'

    def __init__(self, accounts=None, debug=False):
        super(OpenStackWatcher, self).__init__(accounts=accounts, debug=debug)
        self.honor_ephemerals = True
        self.ephemeral_paths = ["updated_at"]

    def _get_openstack_creds(self, account):
        from security_monkey.datastore import Account

        _account = Account.query.filter(Account.name.in_([account])).one()
        return _account.identifier, _account.getCustom('cloudsyaml_file')

    def _get_account_regions(self):
        """ Regions are not global but account specific """
        def _get_regions(cloud_name, yaml_file):
            return [ _region.get('name') for _region in  get_regions( cloud_name, yaml_file ) ]

        account_regions = {}
        for account in self.accounts:
            cloud_name, yaml_file = self._get_openstack_creds(account)
            account_regions[(account, cloud_name, yaml_file)] = _get_regions(cloud_name, yaml_file)
        return account_regions

    def get_name_from_list_output(self, item):
        """ OpenStack allows for duplicate item names in same project for nearly all config types, add id """
        return "{} ({})".format(item.name, item.id) if item.name else item.id

    def get_method(self, item, **kwargs):
        return get_item(item, **kwargs)

    def list_method(self, **kwargs):
        kwargs['service'] = self.service
        kwargs['generator'] = self.generator
        return list_items(**kwargs)

    def _add_exception_fields_to_kwargs(self, **kwargs):
        exception_map = dict()
        kwargs['index'] = self.index
        kwargs['account_name'] = kwargs['account_name']
        kwargs['exception_record_region'] = kwargs['region']
        kwargs['exception_map'] = exception_map
        return kwargs, exception_map

    def slurp(self):
        self.prep_for_slurp()

        @record_exception(source='{index}-watcher'.format(index=self.index), pop_exception_fields=True)
        def invoke_list_method(**kwargs):
            return self.list_method(**kwargs)

        @record_exception(source='{index}-watcher'.format(index=self.index), pop_exception_fields=True)
        def invoke_get_method(item, **kwargs):
            return self.get_method(item, **kwargs)

        @iter_account_region(account_regions=self._get_account_regions())
        def slurp_items(**kwargs):
            kwargs, exception_map = self._add_exception_fields_to_kwargs(**kwargs)

            """ cache some of the kwargs in case they get popped before they are needed """
            region = kwargs['region']
            cloud_name = kwargs['cloud_name']
            account_name = kwargs['account_name']

            results = []
            item_list = invoke_list_method(**kwargs)
            if not item_list:
                return results, exception_map

            for item in item_list:
                item_name = self.get_name_from_list_output(item)
                if item_name and self.check_ignore_list(item_name):
                    continue

                item_details = invoke_get_method(item, **kwargs)
                if item_details:
                    arn = 'arn:openstack:{region}:{cloud_name}:{item_type}/{item_id}'.format(
                        region=region,
                        cloud_name=cloud_name,
                        item_type=self.item_type,
                        item_id=item.id )

                    item = OpenStackChangeItem(index=self.index, account=account_name, region=region, name=item_name, arn=arn,
                                                      config=item_details)
                    results.append(item)
            return results, exception_map
        return self._flatten_iter_response(slurp_items())


class OpenStackChangeItem(CloudAuxChangeItem):
    def __init__(self, index=None, account=None, region=None, name=None, arn=None, config=None, source_watcher=None):
        super(OpenStackChangeItem, self).__init__(
            index=index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            config=config,
            source_watcher=source_watcher)
