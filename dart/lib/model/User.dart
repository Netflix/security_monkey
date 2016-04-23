library security_monkey.user;

import 'Role.dart';
import 'dart:convert';

class User{
  int id;
  String email;
  bool active;
  Role role;
  
  User.fromMap(Map data) {
    id = data['id'];
    email = data['email'];
    active = data['active'];
    
    if(data['role'] != null){
      role = new Role(data['role']);
    }else{
      role = new Role("anonymous");
    }
  }
  
  get role_id => role.id;

  String toJson() {
    Map objmap = {
        "id": id,
        "active": active,
        "email": email,
        "role": role.id,
    };
    return JSON.encode(objmap);
  }
}