library security_monkey.role;

import 'dart:convert';

class Role implements Comparable{
  String id;
  
  Role(String id){
    this.id = id;
  }
  
  Role.fromMap(Map data) {
    id = data['name'];
  }

  String toJson() {
    Map objmap = {
        "name": id
    };
    return JSON.encode(objmap);
  }
  
  bool operator ==(r) => r is Role && this.id == r.id;
  
  int compareTo(Role r){
    return this.id.compareTo(r.id);
  }
}