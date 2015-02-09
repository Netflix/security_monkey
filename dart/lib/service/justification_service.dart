library security_monkey.justification_service;

import 'package:angular/angular.dart';
import 'dart:convert';
import 'dart:async';

import 'package:security_monkey/util/constants.dart';

@Injectable()
class JustificationService {
    final Http _http;
    bool isLoaded = false;
    bool isError = false;
    String errMessage = null;

    JustificationService(this._http);

    Future justify(var issue_id, String justification) {
        String url = '$API_HOST/issues/$issue_id/justification';
        isLoaded = false;

        Map<String, String> requestHeaders = new Map<String, String>();
        requestHeaders['Content-Type'] = 'application/json';

        var jsondata = JSON.encode({
            "justification": justification
        });

        return _http.post(
                url,
                jsondata,
                headers: requestHeaders,
                withCredentials: true,
                xsrfHeaderName: 'X-CSRFToken',
                xsrfCookieName: 'XSRF-COOKIE'
                ).then((HttpResponse response) {
            String resp = response.toString();
            print("Response: $resp");
        }).catchError((error) {
            print("API Puked: $error");
        });
    }

    Future unjustify(var issue_id) {
        String url = '$API_HOST/issues/$issue_id/justification';
        isLoaded = false;

        Map<String, String> requestHeaders = new Map<String, String>();
        requestHeaders['Content-Type'] = 'application/json';

        return _http.delete(
                url,
                headers: requestHeaders,
                withCredentials: true,
                xsrfHeaderName: 'X-CSRFToken',
                xsrfCookieName: 'XSRF-COOKIE'
                ).then((HttpResponse response) {
            String resp = response.toString();
            print("Response: $resp");
        }).catchError((error) {
            print("API Puked: $error");
        });
    }

}
