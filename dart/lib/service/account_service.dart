library security_monkey.account_service;

import 'package:angular/angular.dart';
import 'dart:async';
import 'dart:convert';

import 'package:SecurityMonkey/model/Account.dart';
import 'package:SecurityMonkey/util/constants.dart';

@Injectable()
class AccountService {
  final Http _http;
  Scope scope;
  bool isLoaded=false;
  bool isError = false;
  String errMessage = null;

  AccountService(this._http, this.scope);

  Future<List<Account>> listAccounts() {
    String url = '$API_HOST/accounts/';
    isLoaded = false;
    return _http.get(url, withCredentials:true)
        .then((HttpResponse response) {
      this.isError = false;
      this.errMessage = null;

      print("Response: $response");

      scope.broadcast("username-change", response.data['auth']['user']);
      List<Account> accounts = new List<Account>();

      for (Map acc in response.data['items']) {
        Account account = new Account()
          ..id = acc['id']
          ..active = acc['active']
          ..third_party = acc['third_party']
          ..name = acc['name']
          ..s3_name = acc['s3_name']
          ..number = acc['number']
          ..notes = acc['notes'];
        accounts.add(account);
      }
      isLoaded = true;
      return accounts;
    })
    .catchError((error) {
      this.errMessage = "API unaccessible. $error";
      print(this.errMessage);
      this.isError = true;
      this.isLoaded = false;

      if (error.toString().startsWith("HTTP 401")) {
        if (error is HttpResponse) {
          HttpResponse response = (error as HttpResponse);
          Map authdata = JSON.decode(response.data);
          scope.broadcast("authurl-change", authdata['auth']['url']);
        }
      }
    });
  }

  Future<Account> getAccount(var id) {
    String url = '$API_HOST/account/$id';
    isLoaded = false;
    return _http.get(url, withCredentials:true)
        .then((HttpResponse response) {
      this.isError = false;
      this.errMessage = null;

      scope.broadcast("username-change", response.data['auth']['user']);

      Account account = new Account()
        ..id = response.data['id']
        ..active = response.data['active']
        ..third_party = response.data['third_party']
        ..name = response.data['name']
        ..s3_name = response.data['s3_name']
        ..number = response.data['number']
        ..notes = response.data['notes'];

      isLoaded = true;
      return account;
    })
    .catchError((error) {
      this.errMessage = "API unaccessible. $error";
      print(this.errMessage);
      this.isError = true;
      this.isLoaded = false;

      if (error.toString().startsWith("HTTP 401")) {
        if (error is HttpResponse) {
          HttpResponse response = (error as HttpResponse);
          Map authdata = JSON.decode(response.data);
          scope.broadcast("authurl-change", authdata['auth']['url']);
        }
      }
    });
  }

  Future saveAccount(Account account) {
    int id = account.id;
    String url = '$API_HOST/account/$id';
    isLoaded = false;

    Map<String,String> requestHeaders = new Map<String,String>();
    requestHeaders['Content-Type'] = 'application/json';

    return _http.put(url,
                        account.toJson(),
                        headers: requestHeaders,
                        withCredentials:true)
        .then((HttpResponse response) {
      this.isError = false;
      this.errMessage = null;

      scope.broadcast("username-change", response.data['auth']['user']);
      print("Response: $response");
      isLoaded = true;
    })
    .catchError((error) {
      this.errMessage = "API unaccessible. $error";
      print(this.errMessage);
      this.isError = true;
      this.isLoaded = false;

      if (error.toString().startsWith("HTTP 401")) {
        if (error is HttpResponse) {
          HttpResponse response = (error as HttpResponse);
          Map authdata = JSON.decode(response.data);
          scope.broadcast("authurl-change", authdata['auth']['url']);
        }
      }
    });
  }

  Future<Account> createAccount(Account account) {
      int id = account.id;
      String url = '$API_HOST/account';
      isLoaded = false;

      Map<String,String> requestHeaders = new Map<String,String>();
      requestHeaders['Content-Type'] = 'application/json';

      return _http.post(url,
                          account.toJson(),
                          headers: requestHeaders,
                          withCredentials:true)
          .then((HttpResponse response) {
        this.isError = false;
        this.errMessage = null;

        scope.broadcast("username-change", response.data['auth']['user']);
        print("Response: $response");

        Account account = new Account()
          ..id = response.data['id'];
        return account;
      })
      .catchError((error) {
        this.errMessage = "API unaccessible. $error";
        print(this.errMessage);
        this.isError = true;
        this.isLoaded = false;

        if (error.toString().startsWith("HTTP 401")) {
          if (error is HttpResponse) {
            HttpResponse response = (error as HttpResponse);
            Map authdata = JSON.decode(response.data);
            scope.broadcast("authurl-change", authdata['auth']['url']);
          }
        }
      });
    }

  Future deleteAccount(var id) {
      String url = '$API_HOST/account/$id';
      isLoaded = false;
      return _http.delete(url, withCredentials:true)
          .then((HttpResponse response) {
        this.isError = false;
        this.errMessage = null;
        isLoaded = true;
        scope.broadcast("username-change", response.data['auth']['user']);
      })
      .catchError((error) {
        this.errMessage = "API unaccessible. $error";
        print(this.errMessage);
        this.isError = true;
        this.isLoaded = false;

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