from security_monkey.cloudaux_watcher import CloudAuxWatcher
from security_monkey.cloudaux_watcher import CloudAuxChangeItem
from security_monkey.decorators import record_exception
from cloudaux.decorators import iter_account_region


class CloudAuxBatchedWatcher(CloudAuxWatcher):

    def __init__(self, **kwargs):
        super(CloudAuxBatchedWatcher, self).__init__(**kwargs)
        self.batched_size = 100
        self.done_slurping = False

    def slurp_list(self):
        self.prep_for_batch_slurp()

        @record_exception(source='{index}-watcher'.format(index=self.index), pop_exception_fields=True) 
        def invoke_list_method(**kwargs):
            return self.list_method(**kwargs['conn_dict'])

        @iter_account_region(self.service_name, accounts=self.account_identifiers, 
            regions=self._get_regions(), conn_type='dict')
        def get_item_list(**kwargs):
            kwargs, exception_map = self._add_exception_fields_to_kwargs(**kwargs)
            items = invoke_list_method(**kwargs)

            if not items:
                self.done_slurping = True
                items = list()

            return items, exception_map

        items, exception_map = self._flatten_iter_response(get_item_list())
        self.total_list.extend(items)

        return items, exception_map

    def slurp(self):

        @record_exception(source='{index}-watcher'.format(index=self.index), pop_exception_fields=True) 
        def invoke_get_method(item, **kwargs):
            return self.get_method(item, **kwargs['conn_dict'])

        @iter_account_region(self.service_name, accounts=self.account_identifiers, 
            regions=self._get_regions(), conn_type='dict')
        def slurp_items(**kwargs):
            item_list = list()
            kwargs, exception_map = self._add_exception_fields_to_kwargs(**kwargs)
            item_counter = self.batch_counter * self.batched_size
            while self.batched_size - len(item_list) > 0 and not self.done_slurping:
                cursor = self.total_list[item_counter]
                item_name = self.get_name_from_list_output(cursor)
                if item_name and self.check_ignore_list(item_name):
                    item_counter += 1
                    if item_counter == len(self.total_list):
                        self.done_slurping = True
                    continue
                
                item_details = invoke_get_method(cursor, name=item_name, **kwargs)
                if item_details:
                    item = CloudAuxChangeItem.from_item(
                        name=item_name,
                        item=item_details,
                        override_region=self.override_region, **kwargs)
                    item_list.append(item)
                item_counter += 1
                if item_counter == len(self.total_list):
                    self.done_slurping = True
            self.batch_counter += 1
            return item_list, exception_map 

        return self._flatten_iter_response(slurp_items())
