library security_monkey.itemdetails_service;

import 'package:angular/angular.dart';
import 'dart:async';
import 'dart:convert';

import 'package:SecurityMonkey/model/Item.dart';
import 'package:SecurityMonkey/util/constants.dart';

@Injectable()
class ItemDetailsService {
  final Http _http;
  Scope scope;
  bool isLoaded = false;
  Item item;

  bool isError = false;
  String errMessage = null;

  ItemDetailsService(this._http, this.scope);

  Future loadData(item_id) {
    if (item != null && isLoaded == false) {
      return new Future.value(true);
    }
    String url = '$API_HOST/item/$item_id';
    return _http.get(url, withCredentials:true)
      .then((HttpResponse response) {
          print("Got Item response. Processing...");
          this.isError = false;
          this.errMessage = null;
          item = new Item(response.data);
          scope.broadcast("username-change", response.data['auth']['user']);
          isLoaded = true;
          return item;
        })
        .catchError((error) {
          this.errMessage = "API unaccessible. $error";
          print(this.errMessage);
          this.isError = true;

          if (error.toString().startsWith("HTTP 401")) {
            if (error is HttpResponse) {
              HttpResponse response = (error as HttpResponse);
              Map authdata = JSON.decode(response.data);
              scope.broadcast("authurl-change", authdata['auth']['url']);
            }
          }

        });
  }
}