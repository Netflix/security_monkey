part of security_monkey;

@Component(
        selector: 'issue-table',
        templateUrl: 'packages/security_monkey/component/issue_table_component/issue_table_component.html',
        cssUrl: const ['css/bootstrap.min.css'],
        publishAs: 'cmp')
class IssueTableComponent extends PaginatedTable {
    List<Issue> issues;
    RouteProvider routeProvider;
    Router router;
    Scope scope;
    ObjectStore store;
    bool constructor_complete = false;

    Map<String, String> filter_params = {
        'regions': '',
        'technologies': '',
        'accounts': '',
        'names': '',
        'active': null,
        'searchconfig': null,
        'page': '1',
        'count': '25',
        'enabledonly': true
    };

    IssueTableComponent(this.routeProvider, this.router, Scope scope, this.store)
      : this.scope = scope,
        super(scope) {
        scope.on('close-issue-justification-modal').listen(_justificationModalRequestsRefresh);
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

    String classForJustifyButton() {
        for (Issue issue in issues) {
            if (issue.selected_for_justification) {
                return "";
            }
        }
        return "disabled";
    }

    void openModal() {
        var selectedIssues = [];
        for (Issue issue in issues) {
            if (issue.selected_for_justification) {
                selectedIssues.add(issue);
            }
        }

        scope.rootScope.broadcast("open-issue-justification-modal", selectedIssues);
    }

    void _justificationModalRequestsRefresh(ScopeEvent e) {
        this.list();
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
                super.setPaginationData(issues.meta);
                this.issues = issues;
                super.is_loaded = true;
            });
        }
    }

    void pushFilterRoutes() {
        filter_params = map_to_url(filter_params);
        print("Pushing issue_table_component filter routes: $filter_params");
        router.go('issues', filter_params);
    }

    String classForIssue(Issue issue) {
        if (issue.justified) {
            return "success";
        } else if (issue.score > 3) {
            return "danger";
        } else if (issue.score > 0) {
            return "warning";
        }
        return "";
    }

}
