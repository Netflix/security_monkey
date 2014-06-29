library security_monkey.revision_comment_service;

import 'package:angular/angular.dart';
import 'dart:convert';
import 'dart:async';

import 'package:SecurityMonkey/util/constants.dart';

@Injectable()
class RevisionCommentService {
  final Http _http;
  Scope scope;

  bool isLoaded = false;
  bool isError = false;
  String errMessage = null;

  RevisionCommentService(this._http, this.scope);

  Future addComment(int revision_id, int comment_id, bool isAdding, String comment) {
    String url = '$API_HOST/comment/revision/';
    isLoaded = false;

    Map<String,String> requestHeaders = new Map<String,String>();
    requestHeaders['Content-Type'] = 'application/json';

    String action = isAdding ? "add_comment" : "remove_comment";
    int id = isAdding ? revision_id : comment_id;
    Map objmap = {
                    "comment": comment,
                    "action": action,
                    "id": id
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