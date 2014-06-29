library security_monkey.issues_service;

import 'package:angular/angular.dart';
import 'dart:async';
import 'dart:math';
import 'dart:convert';

import 'package:SecurityMonkey/util/constants.dart';

@Injectable()
class IssuesService {
  final Http _http;
  Scope scope;
  List issues;

  int total_issues = 0;
  int current_page = 1;
  int items_per_page = 25;

  bool isLoaded = false;
  bool isError = false;
  String errMessage = null;

  // Filters
  String region_filter = "";
  String tech_filter = "";
  String account_filter = "";
  String name_filter = "";
  String search = "";

  // Pagination
  int NUMBER_OF_PAGES = 5;
  int start_page = 1;
  int end_page = 1;
  List _pages;

  String active_filter = "";

  get pages => _pages;
  get very_last_page => (total_issues / items_per_page).ceil();
  get getCount => issues.length;

  IssuesService(this._http, this.scope) {
    issues = new List();
    _pages = new List();
  }

  void _updatePagination() {
    start_page = max(current_page - current_page % NUMBER_OF_PAGES, 1);
    if (start_page == 1) {
      end_page = NUMBER_OF_PAGES;
    } else {
      end_page = start_page + NUMBER_OF_PAGES;
    }
    end_page = min(end_page, very_last_page);
    if (start_page == end_page && start_page != 1) {
      start_page = start_page - NUMBER_OF_PAGES;
    }
    print("Start Page: $start_page End Page: $end_page");

    _pages.clear();
    for (var i=start_page; i<= end_page; i++) {
      var active = "";
      if (i == current_page) {
        active = "active";
      }
      _pages.add({'page': i, 'active': active });
    }
  }

  Future loadData(
                  {int count:null,
                   int page:null,
                   String regions: null,
                   String tech:null,
                   String accounts:null,
                   String names:null,
                   String active:null,
                   String search:null}) {
    issues.clear();
    isLoaded=false;
    if (page != null)
      current_page=page;
    if (count != null)
      items_per_page=count;
    if (regions != null)
      region_filter = regions;
    if (tech != null)
      tech_filter = tech;
    if (accounts != null)
      account_filter = accounts;
    if (names != null)
      name_filter = names;

    if (active != null)
      active_filter = "&active=$active";
    else
      active_filter = "";

    if (search != null)
      search = "&q=$search";
    else
      search = "";

    return _loadData(items_per_page,
        current_page,
        region_filter,
        tech_filter,
        account_filter,
        name_filter,
        active_filter,
        search);
  }



  Future _loadData(count, page, regions, tech, accounts, names, active_filter, search) {
    if (issues != null && issues.length > 0) {
      return new Future.value(true);
    }
    // TODO: These variables should be URL encoded.
    String url = '$API_HOST/issues/?count=$count&page=$page&regions=$regions&technologies=$tech&accounts=$accounts&names=$names$active_filter$search';
    print("_loadData::Connecting to url: $url");
    return _http.get(url, withCredentials:true)
          .then((HttpResponse response) {
          print("Got response. Processing...");
          this.isError = false;
          this.errMessage = null;
          total_issues = response.data['total'];
          current_page = response.data['page'];
          for (var item in response.data['items']) {
            issues.add(item); // new Issue(item));
          }
          scope.broadcast("username-change", response.data['auth']['user']);
          var rcount = issues.length;
          print("Added $rcount items");
          _updatePagination();
          isLoaded = true;
      })
      .catchError((error) {
        print("Error: $error");
        if (error.toString().startsWith("HTTP 401")) {
          if (error is HttpResponse) {
            HttpResponse response = (error as HttpResponse);
            Map authdata = JSON.decode(response.data);
            scope.broadcast("authurl-change", authdata['auth']['url']);
          }
        } else {
          this.errMessage = "API unaccessible. $error";
          print(this.errMessage);
          this.isError = true;
        }
      });
  }

}