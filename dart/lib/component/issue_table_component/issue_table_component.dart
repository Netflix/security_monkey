library security_monkey.issue_table_component;

import 'package:angular/angular.dart';

import 'package:SecurityMonkey/model/Issue.dart';
import 'package:SecurityMonkey/routing/securitymonkey_router.dart' show param_from_url, param_to_url, map_from_url, map_to_url;
import 'package:SecurityMonkey/component/paginated_table/paginated_table.dart';
import 'package:hammock/hammock.dart';

@Component(selector: 'issue-table', templateUrl: 'packages/SecurityMonkey/component/issue_table_component/issue_table_component.html', cssUrl: const ['css/bootstrap.min.css'], publishAs: 'cmp')
class IssueTableComponent extends PaginatedTable {
    List<Issue> issues;
    RouteProvider routeProvider;
    Router router;
    Scope scope;
    ObjectStore store;
    bool constructor_complete = false;

    Map<String, String> filter_params = {
        'filterregions': '',
        'filtertechnologies': '',
        'filteraccounts': '',
        'filternames': '',
        'filteractive': null,
        'searchconfig': null,
        'page': '1',
        'count': '25'
    };

    IssueTableComponent(this.routeProvider, this.router, this.scope, this.store) {
        super.setupTable(scope);
        scope.on("issues-pagination").listen(super.setPaginationData);
        filter_params = map_from_url(filter_params, this.routeProvider);

        // The AngularUI Pagination tries to correct the currentPage value
        // to page 1 when the API server hasn't yet responded with results.
        // To fix, don't set the currentPage variable until we have received
        // a response from the API server containing totalItems.
        store.list(Issue, params: {
            "count": filter_params['count'],
            "page": filter_params['page']
        }).then((issues) {
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
            store.list(Issue, params: {
                "count": ipp_as_int,
                "page": currentPage
            }).then((issues) {
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
