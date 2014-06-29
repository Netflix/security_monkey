library security_monkey.justify_service;

import 'package:angular/angular.dart';
import 'dart:convert';
import 'dart:async';

import 'package:SecurityMonkey/util/constants.dart';

@Injectable()
class JustifyService {
  final Http _http;
  Scope scope;

  bool isLoaded = false;
  bool isError = false;
  String errMessage = null;

  JustifyService(this._http, this.scope);

  Future justify(var issue_id, bool isJustifying, String justification) {
    String url = '$API_HOST/justify/$issue_id';
    isLoaded = false;

    Map<String,String> requestHeaders = new Map<String,String>();
    requestHeaders['Content-Type'] = 'application/json';

    String action = isJustifying ? "justify" : "remove_justification";
    Map objmap = {
                    "justification": justification,
                    "action": action
                  };
    var jsondata = JSON.encode(objmap);


    return _http.post(
            url,
            jsondata,
            headers: requestHeaders,
            withCredentials:true
        )
      .then((HttpResponse response) {
        String resp = response.toString();
        print("Response: $resp");
      }).catchError((error) {
        print("API Puked: $error");
      });
  }

}