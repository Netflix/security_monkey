library security_monkey.username_service;

import 'package:angular/angular.dart';
import 'dart:async';
import 'dart:html';

@Injectable()
class UsernameService {

  String name = "";
  Scope scope;

  UsernameService(this.scope) {
    //http://stackoverflow.com/questions/22151427/how-to-communicate-between-angular-dart-controllers
    Stream username_change_stream = scope.on('username-change');
    username_change_stream.listen(usernameChange);

    Stream authurl_change_stream = scope.on('authurl-change');
    authurl_change_stream.listen(authURLChange);
  }

  void authURLChange(ScopeEvent e) {
    String auth_url = e.data;
    if(auth_url.isNotEmpty) {
      window.location.assign(auth_url);
    }
  }

  void usernameChange(ScopeEvent e) {
    this.name = e.data;
  }

  get signed_in => name.isNotEmpty;

}


//  // sender
//  scope.emit("username-change", "emit");
//  scope.broadcast("username-change", "broadcast");
//  scope.parentScope.broadcast("username-change", "parent-broadcast");
//  scope.rootScope.broadcast("username-change", "root-broadcast");
//
//  scope.$emit('my-event-name', [someData, someOtherData]); // propagate towards root
//  scope.$broadcast('my-event-name', [someData, someOtherData]); // propagate towards leaf nodes (children)
//  scope.$parent.$broadcast('my-event-name', [someData, someOtherData]); // send to parents childs (includes silblings children)
//  scope.$root.$broadcast('my-event-name', [someData, someOtherData]); // propagate towards leaf nodes starting from root (all nodes)
//
//  // receiver
//  scope.$on('my-event-name', (ScopeEvent e) => myCallback(e)); // call myCallback when an `my-event-name` event reaches me
