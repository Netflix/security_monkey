part of security_monkey;

@Component(
    selector: 'item-table',
    templateUrl: 'packages/security_monkey/component/item_table_component/item_table_component.html',
    cssUrl: const ['css/bootstrap.min.css'],
    publishAs: 'cmp')
class ItemTableComponent extends PaginatedTable implements DetachAware {
    List<Item> items;
    RouteProvider routeProvider;
    Router router;
    Scope scope;
    ObjectStore store;
    bool constructor_complete = false;
    bool _autorefresh = false;
    Timer autorefresh_timer;

    @override
    void detach() {
        if (autorefresh_timer != null) {
            autorefresh_timer.cancel();
            autorefresh_timer = null;
        }
    }

    Map<String, String> filter_params = {
        'regions': '',
        'technologies': '',
        'accounts': '',
        'names': '',
        'active': null,
        'searchconfig': null,
        'page': '1',
        'count': '25'
    };

    ItemTableComponent(this.routeProvider, this.router, Scope scope, this.store)
      : this.scope=scope,
      super(scope) {
        filter_params = map_from_url(filter_params, this.routeProvider);
        store.list(Item, params: filter_params).then((items) {
            super.setPaginationData(items.meta);
            this.items = items;
            super.is_loaded = true;
            super.items_per_page = filter_params['count'];
            super.currentPage = int.parse(filter_params['page']);
            constructor_complete = true;
        });
    }


    /// Case 1 - Item has no issues or scoreless issues. Return "";
    /// Case 2 - Item has all justified issues. Return "success";
    /// Case 3 - Item has unjustified issues w/score <=3. Return "warning";
    /// Case 4 - Item has unjustified issues w/score >3. Return "danger";
    String classForItem(Item item) {
        if (item.number_issues == 0 || item.totalScore() == 0) {
            return "";
        }

        if (item.unjustifiedScore() == 0) {
            return "success";
        }

        if (item.unjustifiedScore() <= 3) {
            return "warning";
        }

        return "danger";

    }

    void list() {
        if (!constructor_complete) {
            return;
        }
        super.is_loaded = false;
        if (filter_params['page'] != super.currentPage.toString() || filter_params['count'] != super.items_per_page) {
            filter_params['page'] = super.currentPage.toString();
            filter_params['count'] = super.items_per_page;
            this.pushFilterRoutes();
        } else {
            print("Loading Filtered Data.");
            store.list(Item, params: filter_params).then((items) {
                super.setPaginationData(items.meta);
                this.items = items;
                super.is_loaded = true;
            });
        }

    }

    void pushFilterRoutes() {
        filter_params = map_to_url(filter_params);
        print("Pushing item_table_component filter routes: $filter_params");
        router.go('items', filter_params);
    }

    get autorefresh => _autorefresh;
    set autorefresh(bool ar) {
        _autorefresh = ar;
        if (_autorefresh) {
            autorefresh_timer = new Timer.periodic(new Duration(seconds: 30), (_) {
                this.list();
            });
        } else {
            autorefresh_timer.cancel();
            autorefresh_timer = null;
        }
    }
}
