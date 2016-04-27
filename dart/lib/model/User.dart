library security_monkey.user;

import 'Role.dart';
import 'dart:convert';
import 'package:security_monkey/util/utils.dart' show localDateFromAPIDate;

class User{
  int id;
  String email;
  bool active;
  Role role;
  DateTime confirmed_at;
  int login_count;
  DateTime last_login_at;
  DateTime current_login_at;
  String last_login_ip;
  String current_login_ip;
  bool daily_audit_email;
  String change_reports;


  User.fromMap(Map data) {
    id = data['id'];
    email = data['email'];
    active = data['active'];

    if(data['role'] != null){
      role = new Role(data['role']);
    }else{
      role = new Role("anonymous");
    }

    if(data['confirmed_at'] != null) {
      confirmed_at = localDateFromAPIDate(data['confirmed_at']);
    }
    login_count = data['login_count'];
    if(data['last_login_at'] != null) {
      last_login_at = localDateFromAPIDate(data['last_login_at']);
    }
    if(data['current_login_at']) {
      current_login_at = localDateFromAPIDate(data['current_login_at']);
    }
    last_login_ip = data['last_login_ip'];
    current_login_ip = data['current_login_ip'];
    daily_audit_email = data['daily_audit_email'];
    change_reports = data['change_reports'];
  }

  get role_id => role.id;

  String toJson() {
    Map objmap = {
        "id": id,
        "active": active,
        "email": email,
        "role": role.id
    };
    return JSON.encode(objmap);
  }
}
