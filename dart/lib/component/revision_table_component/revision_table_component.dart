library security_monkey.revision_table_component;

import 'package:angular/angular.dart';
import 'dart:math';

import 'package:SecurityMonkey/service/revisions_service.dart';
import 'package:SecurityMonkey/routing/securitymonkey_router.dart' show param_from_url, param_to_url, map_from_url, map_to_url;

@Component(
    selector: 'revision-table',
    templateUrl: 'packages/SecurityMonkey/component/revision_table_component/revision_table_component.html',
    cssUrl: const ['css/bootstrap.min.css'],
    publishAs: 'cmp')
class RevisionTableComponent {
  RevisionsService rs;
  RouteProvider routeProvider;
  Router router;
  Scope scope;

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

  RevisionTableComponent(this.routeProvider, this.rs, this.router, this.scope)  {
    filter_params = map_from_url(filter_params, this.routeProvider);
    // Make sure the items_per_page dropdown displays the number
    // of items we were told to display from the URL.
    this._items_per_page = int.parse(filter_params['count']);
    update_filters();
  }

  String items_displayed() {
      // return 1-25 or 26-27
    int start = (rs.current_page-1) * _items_per_page + 1;
    int end = start + rs.revisions.length - 1;
    return "$start-$end";
  }

  void update_filters() {
    print("Loading Filtered Data...");
    rs.loadData(
        count: int.parse(this.filter_params['count']),
        page: int.parse(this.filter_params['page']),
        regions: this.filter_params['filterregions'],
        tech: this.filter_params['filtertechnologies'],
        accounts: this.filter_params['filteraccounts'],
        names: this.filter_params['filternames'],
        active: this.filter_params['filteractive'],
        searchconfig: this.filter_params['searchconfig']
        ).then((_) {
          print("Done loading data.");
    });
  }

  void pushFilterRoutes() {
    filter_params = map_to_url(filter_params);
    print("Pushing revision_table_component filter routes: $filter_params");
    router.go('revisions', filter_params);
  }

  void view_item(item_id, revision_id) {
    this.router.go('viewitemrevision', {'itemid': item_id, 'revid': revision_id});
  }

  get revisionsLoaded => rs.isLoaded;
  get revision_current_page_count => rs.getRevisionCount;
  get revisions => rs.revisions;
  get current_page => rs.current_page;
  get total_revisions => rs.total_revisions;
  get isError => rs.isError;
  get errMessage => rs.errMessage;

  // Pagination options
  List<String> items_per_page_options = ['25', '50', '100', '250', '1000'];

  int _items_per_page = 25;
  get items_per_page => _items_per_page.toString();
  set items_per_page(ipp) {
    _items_per_page = int.parse(ipp);
    changeItemsPerPage();
  }

  get pages => rs.pages;
  get very_last_page => rs.very_last_page;

  get more_than_one_page => rs.pages.length > 1 ? true : false;

  void getNextPage() {
    int np = rs.current_page + 1;
    if (np > rs.very_last_page)
      return;
    load_page(np);
  }

  void getPrevPage() {
    int np = rs.current_page - 1;
    if (np < 1)
      return;
    load_page(np);
  }

  void load_page(int n) {
    if (n == rs.current_page) {
      return;
    }
    this.filter_params['page'] = n.toString();
    this.pushFilterRoutes();
  }

  void changeItemsPerPage() {
    print("Items: $items_per_page");

    // When resized, make sure the new page number isn't out of bounds.
    // Also, try to keep them at about the same place in the dataset.
    int new_very_last_page = (rs.total_revisions / _items_per_page).ceil();
    int new_current_page = ((rs.current_page / rs.very_last_page) * new_very_last_page).toInt();
    new_current_page = max(1, new_current_page);

    print("Loading data...[$items_per_page]");
    this.filter_params['count'] = items_per_page;
    this.filter_params['page'] = new_current_page.toString();
    this.pushFilterRoutes();
  }
}