part of security_monkey;

@Component(
        selector: 'justified-table',
        templateUrl: 'packages/security_monkey/component/justified_table_component/justified_table_component.html',
        useShadowDom: false
)
class JustifiedTableComponent extends PaginatedTable implements ScopeAware {
    List<Issue> issues = [];
    RouteProvider routeProvider;
    Router router;
    ObjectStore store;
    bool constructor_complete = false;
    Scope _scope;

    Map<String, String> filter_params = {
        'regions': '',
        'technologies': '',
        'accounts': '',
        'accounttypes': '',
        'names': '',
        'arns': '',
        'active': null,
        'searchconfig': null,
        'page': '1',
        'count': '25',
        'enabledonly': 'true',
        'justified': true
    };

    JustifiedTableComponent(this.routeProvider, this.router, this.store) {
        filter_params = map_from_url(filter_params, this.routeProvider);

        /// The AngularUI Pagination tries to correct the currentPage value
        /// to page 1 when the API server hasn't yet responded with results.
        /// To fix, don't set the currentPage variable until we have received
        /// a response from the API server containing totalItems.
        store.list(Issue, params: filter_params).then((issues) {
            super.setPaginationData(issues.meta);
            this.issues = issues;
            super.is_loaded = true;
            super.items_per_page = filter_params['count'];
            super.currentPage = int.parse(filter_params['page']);
            constructor_complete = true;
        });
    }

    void list() {
        if (!constructor_complete) {
            return;
        }
        if (filter_params['page'] != super.currentPage.toString() || filter_params['count'] != super.items_per_page) {
            filter_params['page'] = super.currentPage.toString();
            filter_params['count'] = super.items_per_page;
            this.pushFilterRoutes();
        } else {
            print("Loading Filtered Data.");
            store.list(Issue, params: filter_params).then((issues) {
                super.setPaginationData(justifiled_issues.meta);
                this.issues = issues;
                super.is_loaded = true;
            });
        }
    }

    void pushFilterRoutes() {
        filter_params = map_to_url(filter_params);
        print("Pushing justified_table_component filter routes: $filter_params");
        router.go('justified', filter_params);
    }

}
