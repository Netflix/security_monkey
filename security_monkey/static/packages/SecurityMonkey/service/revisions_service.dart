library security_monkey.revisions_service;

import 'package:angular/angular.dart';
import 'dart:async';
import 'dart:math';
import 'dart:convert';

import 'package:SecurityMonkey/model/Revision.dart';
import 'package:SecurityMonkey/util/constants.dart';

@Injectable()
class RevisionsService {
  final Http _http;
  Scope scope;
  bool isLoaded = false;
  List<Revision> revisions;
  int total_revisions = 0;
  int current_page = 1;
  int items_per_page = 25;

  bool isError = false;
  String errMessage = null;

  // Filters
  String region_filter = "";
  String tech_filter = "";
  String account_filter = "";
  String name_filter = "";
  String searchconfig = "";

  // Active_filter has three states:
  //    "" - no filtering
  //    "True" - only return active items
  //    Anything else - only show inactive items
  String active_filter = "";

  // Pagination
  int NUMBER_OF_PAGES = 5;
  int start_page = 1;
  int end_page = 1;
  List _pages;

  get pages => _pages;
  get very_last_page => (total_revisions / items_per_page).ceil();

  RevisionsService(this._http, this.scope) {
    revisions = new List<Revision>();
    _pages = new List();
  }

  Future loadData(
                  {int count:null,
                   int page:null,
                   String regions: null,
                   String tech:null,
                   String accounts:null,
                   String names:null,
                   String active:null,
                   String searchconfig:null}) {
    revisions.clear();
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

    if (searchconfig != null)
      searchconfig = "&searchconfig=$searchconfig";
    else
      searchconfig = "";

    return _loadData(items_per_page,
        current_page,
        region_filter,
        tech_filter,
        account_filter,
        name_filter,
        active_filter,
        searchconfig);
  }



  Future _loadData(count, page, regions, tech, accounts, names, active_filter, searchconfig) {
    if (revisions != null && revisions.length > 0) {
      return new Future.value(true);
    }
    // TODO: These variables should be URL encoded.
    String url = '$API_HOST/revisions/?count=$count&page=$page&regions=$regions&technologies=$tech&accounts=$accounts&names=$names$active_filter$searchconfig';
    print("_loadData::Connecting to url: $url");
    return _http.get(url, withCredentials:true)
          .then((HttpResponse response) {
          print("Got response. Processing...");
          this.isError = false;
          this.errMessage = null;
          total_revisions = response.data['total'];
          current_page = response.data['page'];
          for (var item in response.data['items']) {
            revisions.add(new Revision(item));
          }
          scope.broadcast("username-change", response.data['auth']['user']);
          var rcount = revisions.length;
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

  get getRevisionCount => revisions.length;

}