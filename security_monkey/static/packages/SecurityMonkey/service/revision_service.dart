library security_monkey.revision_service;

import 'package:angular/angular.dart';
import 'dart:async';
import 'dart:convert';

import 'package:SecurityMonkey/model/Revision.dart';
import 'package:SecurityMonkey/util/constants.dart';

@Injectable()
class RevisionService {
  final Http _http;
  Scope scope;
  bool isLoaded = false;
  Map<dynamic, Revision> revisions;

  bool isError = false;
  String errMessage = null;

  RevisionService(this._http, this.scope) {
    revisions = new Map<dynamic, Revision>();

  }

  Future<Revision> loadData(revision_id, [compare_id]) {
    if (revisions[revision_id] != null && isLoaded == false) {
      return new Future.value(revisions[revision_id]);
    }
    String url = '$API_HOST/revision/$revision_id';
    if (compare_id != null) {
      url = '$url?compare=$compare_id';
    }
    return _http.get(url, withCredentials:true)
          .then((HttpResponse response) {
          print("Got Item response. Processing...");
          this.isError = false;
          this.errMessage = null;
          Revision revision = new Revision(response.data);
          scope.broadcast("username-change", response.data['auth']['user']);
          isLoaded = true;
          revisions[revision_id] = revision;
          return revision;
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