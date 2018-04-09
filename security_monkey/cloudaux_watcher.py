from security_monkey.watcher import Watcher, ChangeItem
from security_monkey.decorators import record_exception
from cloudaux.decorators import iter_account_region
from security_monkey import AWS_DEFAULT_REGION


class CloudAuxWatcher(Watcher):
    index = 'abstract'
    i_am_singular = 'Abstract Watcher'
    i_am_plural = 'Abstract Watchers'
    honor_ephemerals = False
    ephemeral_paths = ['_version']
    override_region = None
    service_name = None

    def list_method(self, **kwargs):
        raise Exception('Not Implemented')

    def get_method(self, item, **kwargs):
        raise Exception('Not Implemented')

    def get_name_from_list_output(self, item):
        return item['Name']

    def __init__(self, accounts=None, debug=None):
        super(CloudAuxWatcher, self).__init__(accounts=accounts, debug=debug)

    def _get_account_name(self, identifier):
        idx = 0
        for ident in self.account_identifiers:
            if ident == identifier:
                return self.accounts[idx]

    def _get_assume_role(self, identifier):
        from security_monkey.datastore import Account
        account = Account.query.filter(Account.identifier == identifier).first()
        return account.getCustom("role_name") or 'SecurityMonkey'

    def _get_regions(self):
        from security_monkey.decorators import get_regions
        from security_monkey.datastore import Account
        # pick an arbitrary account:
        identifier = self.account_identifiers[0]
        account = Account.query.filter(Account.identifier == identifier).first()
        _, regions = get_regions(account, self.service_name)
        return regions

    def _add_exception_fields_to_kwargs(self, **kwargs):
        exception_map = dict()
        kwargs['index'] = self.index
        kwargs['account_name'] = self._get_account_name(kwargs['conn_dict']['account_number'])
        kwargs['exception_record_region'] = self.override_region or kwargs['conn_dict']['region']
        kwargs['exception_map'] = exception_map
        kwargs['conn_dict']['assume_role'] = self._get_assume_role(kwargs['conn_dict']['account_number'])
        del kwargs['conn_dict']['tech']
        del kwargs['conn_dict']['service_type']
        return kwargs, exception_map

    def _flatten_iter_response(self, response):
        """
        The cloudaux iter_account_region decorator returns a list of tuples.
        Each tuple contains two members.  1) The result. 2) The exception map.
        This method combines that list of tuples into a single result list and a single exception map.
        """
        items = list()
        exception_map = dict()
        for result in response:
            items.extend(result[0])
            exception_map.update(result[1])
        return items, exception_map

    def slurp(self):
        self.prep_for_slurp()

        @record_exception(source='{index}-watcher'.format(index=self.index), pop_exception_fields=True)
        def invoke_list_method(**kwargs):
            return self.list_method(**kwargs['conn_dict'])

        @record_exception(source='{index}-watcher'.format(index=self.index), pop_exception_fields=True)
        def invoke_get_method(item, **kwargs):
            return self.get_method(item, **kwargs['conn_dict'])

        @iter_account_region(self.service_name, accounts=self.account_identifiers,
                             regions=self._get_regions(), conn_type='dict')
        def slurp_items(**kwargs):
            kwargs, exception_map = self._add_exception_fields_to_kwargs(**kwargs)

            results = []
            item_list = invoke_list_method(**kwargs)
            if not item_list:
                return results, exception_map

            for item in item_list:
                item_name = self.get_name_from_list_output(item)
                if item_name and self.check_ignore_list(item_name):
                    continue

                item_details = invoke_get_method(item, name=item_name, **kwargs)
                if item_details:
                    # Has the item name been updated? (Things like Security Groups and VPCs have friendlier names
                    # than just their ID's:
                    item_name = item_details.pop("DEFERRED_ITEM_NAME", item_name)

                    # Determine which region to record the item into.
                    # Some tech, like IAM, is global and so we record it as 'universal' by setting an override_region
                    # Some tech, like S3, requires an initial connection to us-east-1, though a buckets actual
                    # region may be different. Extract the actual region from item_details.
                    # Otherwise, just use the region where the boto connection was made.
                    record_region = self.override_region or \
                        item_details.get('Region') or kwargs['conn_dict']['region']
                    item = CloudAuxChangeItem.from_item(
                        name=item_name,
                        item=item_details,
                        record_region=record_region,
                        source_watcher=self,
                        **kwargs)
                    results.append(item)

            return results, exception_map

        return self._flatten_iter_response(slurp_items())


class CloudAuxChangeItem(ChangeItem):
    def __init__(self, index=None, account=None, region=AWS_DEFAULT_REGION, name=None, arn=None, config=None,
                 source_watcher=None):
        super(CloudAuxChangeItem, self).__init__(
            index=index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config if config else {},
            source_watcher=source_watcher)

    @classmethod
    def from_item(cls, name, item, record_region, source_watcher=None, **kwargs):
        return cls(
            name=name,
            arn=item['Arn'],
            account=kwargs.get('account_name', kwargs.get('ProjectId')),
            index=kwargs['index'],
            region=record_region,
            config=item,
            source_watcher=source_watcher)
