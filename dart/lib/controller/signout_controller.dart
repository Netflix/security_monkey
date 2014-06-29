library signout_controller;
import 'package:angular/angular.dart';
import 'package:SecurityMonkey/util/constants.dart';


@Controller(
    selector: '[signout]',
    publishAs: 'signout_ctrl')
class SignoutController {
  // On init, make a call to /logout on API
  final Http _http;
  Scope scope;
  bool complete = false;
  bool error = false;
  bool loading = true;

  SignoutController(this._http, this.scope) {
    String url = '$API_HOST/logout';
    print("Signing Out...");
    _http.get(url, withCredentials:true)
      .then((HttpResponse response) {
      print("Sign Out Complete");
      complete = true;
      loading = false;
//      scope.emit("username-change", "emit");
//      scope.broadcast("username-change", "broadcast");
//      scope.parentScope.broadcast("username-change", "parent-broadcast");
      scope.rootScope.broadcast("username-change", "");
    })
    .catchError((error) {
      print("Error Signing Out $error");
      error = true;
      loading = false;
    });
  }
}
