library security_monkey.issue_table_component;

import 'package:angular/angular.dart';
//import 'dart:math';

import 'package:SecurityMonkey/service/issues_service.dart';
import 'package:SecurityMonkey/service/justify_service.dart';
import 'package:SecurityMonkey/routing/securitymonkey_router.dart' show param_from_url, param_to_url, map_from_url, map_to_url;
import 'package:SecurityMonkey/component/paginated_table/paginated_table.dart';

@Component(
    selector: 'issue-table',
    templateUrl: 'packages/SecurityMonkey/component/issue_table_component/issue_table_component.html',
    cssUrl: const ['css/bootstrap.min.css'],
    publishAs: 'cmp')
class IssueTableComponent extends PaginatedTable {
  IssuesService iss;
  JustifyService js;
  RouteProvider routeProvider;
  Router router;
  Scope scope;
  bool constructor_complete=false;

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

  IssueTableComponent(this.routeProvider, this.iss, this.js, this.router, this.scope) {
    super.setupTable(scope);
    scope.on("issues-pagination").listen(super.setPaginationData);
    filter_params = map_from_url(filter_params, this.routeProvider);
    super.items_per_page = filter_params['count'];
    super.currentPage = int.parse(filter_params['page']);
    constructor_complete=true;
    this.list();
  }

  void list() {
    if (!constructor_complete) {
      return;
    }
    if (filter_params['page'] != super.currentPage.toString()
        || filter_params['count'] != super.items_per_page) {
      filter_params['page'] = super.currentPage.toString();
      filter_params['count'] = super.items_per_page;
      this.pushFilterRoutes();
    } else {

      print("Loading Filtered Data.");
      iss.loadData(
          count: super.ipp_as_int,
          page: super.currentPage,
          regions: this.filter_params['filterregions'],
          tech: this.filter_params['filtertechnologies'],
          accounts: this.filter_params['filteraccounts'],
          names: this.filter_params['filternames'],
          active: this.filter_params['filteractive'],
          search: this.filter_params['searchconfig']
          ).then((_) {
            print("Done loading data.");
      });
    }
  }

  void pushFilterRoutes() {
    filter_params = map_to_url(filter_params);
    print("Pushing issue_table_component filter routes: $filter_params");
    router.go('issues', filter_params);
  }

//  void view_item(item_id) {
//    this.router.go('viewitem', {'itemid': item_id});
//  }

  // comment out when moving to hammock.
  String items_displayed() {
   // return 1-25 or 26-27
   int start = (iss.current_page-1) * super.ipp_as_int + 1;
   int end = start + iss.issues.length - 1;
   return "$start-$end";
  }

  String classForIssue(Map issue) {
   // ""
   // warning
   // danger
   if(issue['justified']) {
     return "success";
   }
   if(issue['score'] > 3) {
     return "danger";
   }
   if(issue['score'] > 0) {
     return "warning";
   }
   return "";
  }

  get isLoaded => iss.isLoaded;
  get current_page_count => iss.getCount;
  get issues => iss.issues;
  get current_page => iss.current_page;
  get total_issues => iss.total_issues;
  get isError => iss.isError;
  get errMessage => iss.errMessage;
}