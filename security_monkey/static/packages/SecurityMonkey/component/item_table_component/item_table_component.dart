library item_table_component;

import 'package:angular/angular.dart';
import 'dart:math';

import 'package:SecurityMonkey/service/items_service.dart' show ItemsService;
import 'package:SecurityMonkey/routing/securitymonkey_router.dart' show param_from_url, param_to_url, map_from_url, map_to_url;
import 'package:SecurityMonkey/model/Item.dart';

@Component(
    selector: 'item-table',
    templateUrl: 'packages/SecurityMonkey/component/item_table_component/item_table_component.html',
    cssUrl: const ['css/bootstrap.min.css'],
    publishAs: 'cmp')
class ItemTableComponent {
  ItemsService its;
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

  ItemTableComponent(this.routeProvider, this.its, this.router, this.scope)  {
    filter_params = map_from_url(filter_params, this.routeProvider);
    // Make sure the items_per_page dropdown displays the number
    // of items we were told to display from the URL.
    this._items_per_page = int.parse(filter_params['count']);
    update_filters();
  }

  String items_displayed() {
    // return 1-25 or 26-27
    int start = (its.current_page-1) * _items_per_page + 1;
    int end = start + its.items.length - 1;
    return "$start-$end";
  }

  String classForItem(Item item) {
    // ""
    // warning
    // danger
    if(item.totalScore() > 0) {
      return "danger";
    }
    if(item.number_issues > 0) {
      return "warning";
    }
    return "";
  }

  void update_filters() {
    print("Loading Filtered Data...");
    its.loadData(
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
    print("Pushing item_table_component filter routes: $filter_params");
    router.go('items', filter_params);
  }

  void view_item(item_id) {
    this.router.go('viewitem', {'itemid': item_id });
  }

  get itemsLoaded => its.isLoaded;
  get item_current_page_count => its.getItemCount;
  get items => its.items;
  get current_page => its.current_page;
  get total_items => its.total_items;
  get isError => its.isError;
  get errMessage => its.errMessage;

  // Pagination options
  List<String> items_per_page_options = ['25', '50', '100', '250', '1000'];

  int _items_per_page = 25;
  get items_per_page => _items_per_page.toString();
  set items_per_page(ipp) {
    _items_per_page = int.parse(ipp);
    changeItemsPerPage();
  }

  get pages => its.pages;
  get very_last_page => its.very_last_page;

  get more_than_one_page => its.pages.length > 1 ? true : false;

  void getNextPage() {
    int np = its.current_page + 1;
    if (np > its.very_last_page)
      return;
    load_page(np);
  }

  void getPrevPage() {
    int np = its.current_page - 1;
    if (np < 1)
      return;
    load_page(np);
  }

  void load_page(int n) {
    if (n == its.current_page) {
      return;
    }
    this.filter_params['page'] = n.toString();
    this.pushFilterRoutes();
  }

  void changeItemsPerPage() {
    print("Items: $items_per_page");

    // When resized, make sure the new page number isn't out of bounds.
    // Also, try to keep them at about the same place in the dataset.
    int new_very_last_page = (its.total_items / _items_per_page).ceil();
    int new_current_page = ((its.current_page / its.very_last_page) * new_very_last_page).toInt();
    new_current_page = max(1, new_current_page);

    print("Loading data...[$items_per_page]");
    this.filter_params['count'] = items_per_page;
    this.filter_params['page'] = new_current_page.toString();
    this.pushFilterRoutes();
  }
}