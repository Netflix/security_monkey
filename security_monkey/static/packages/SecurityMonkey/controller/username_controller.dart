library security_monkey.username_controller;

import 'package:angular/angular.dart';
import 'package:SecurityMonkey/service/username_service.dart';

@Controller(
    selector: '[username]',
    publishAs: 'user_ctrl')
class UsernameController {
  UsernameService us;
  UsernameController(this.us);

  get name => this.us.name;
  get signed_in => this.us.signed_in;

}