library security_monkey.user_settings_service;

import 'package:angular/angular.dart';
import 'dart:async';
import 'dart:convert';

import 'package:SecurityMonkey/model/UserSetting.dart';
import 'package:SecurityMonkey/util/constants.dart';
import 'package:SecurityMonkey/model/Account.dart';

@Injectable()
class UserSettingsService {
  final Http _http;
  Scope scope;
  UserSetting user_setting;

  UserSettingsService(this._http, this.scope) {
    print("$API_HOST");
    load_data().then((_) {
      this.isLoaded = true;
    });
  }

  bool isLoaded = false;
  bool isError = false;
  String errMessage = null;


  Future load_data() {
    String url = '$API_HOST/settings';
    print("Loading settings from $url");

    isLoaded = false;
    return _http.get(url, withCredentials:true)
          .then((HttpResponse response) {
      this.isError = false;
      this.errMessage = null;

      scope.broadcast("username-change", response.data['auth']['user']);

      for (Map setting in response.data['settings']) {
        user_setting = new UserSetting()
          //..accounts = setting['accounts']
          ..daily_audit_email = setting['daily_audit_email']
          ..change_report_setting = setting['change_reports'];

        for (var account_id in setting['accounts']) {
          Account account = new Account()
            ..id = account_id;
          user_setting.accounts.add(account);
        }

        print("added usersetting $user_setting");
      }
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

  Future saveSettings() {
    String url = '$API_HOST/settings';

    Map<String,String> requestHeaders = new Map<String,String>();
    requestHeaders['Content-Type'] = 'application/json';
    isLoaded = false;

    return _http.post(
                url,
                this.user_setting.toJson(),
                headers: requestHeaders,
                withCredentials:true
            )
          .then((HttpResponse response) {
            String resp = response.toString();
            print("Response: $resp");
            isLoaded = true;
          }).catchError((error) {
            print("API Puked: $error");
            isError = true;
            errMessage = error;
          });
  }


}