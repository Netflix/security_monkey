part of security_monkey;

@Component(
    selector: 'revision-table',
    templateUrl: 'packages/SecurityMonkey/component/revision_table_component/revision_table_component.html',
    cssUrl: const ['css/bootstrap.min.css'],
    publishAs: 'cmp')
class RevisionTableComponent extends PaginatedTable implements DetachAware {
    List<Revision> revisions;
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

    RevisionTableComponent(this.routeProvider, this.router, this.scope, this.store) {
        super.setupTable(scope);
        scope.on("revisions-pagination").listen(super.setPaginationData);
        filter_params = map_from_url(filter_params, this.routeProvider);

        // The AngularUI Pagination tries to correct the currentPage value
        // to page 1 when the API server hasn't yet responded with results.
        // To fix, don't set the currentPage variable until we have received
        // a response from the API server containing totalItems.
        store.list(Revision, params: filter_params).then((revisions) {
            this.revisions = revisions;
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
        super.is_loaded = false;
        if (filter_params['page'] != super.currentPage.toString() || filter_params['count'] != super.items_per_page) {
            filter_params['page'] = super.currentPage.toString();
            filter_params['count'] = super.items_per_page;
            this.pushFilterRoutes();
        } else {
            print("Loading Filtered Data.");
            store.list(Revision, params: filter_params).then((revisions) {
                this.revisions = revisions;
                super.is_loaded = true;
            });
        }
    }

    void pushFilterRoutes() {
        filter_params = map_to_url(filter_params);
        print("Pushing revision_table_component filter routes: $filter_params");
        router.go('revisions', filter_params);
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
