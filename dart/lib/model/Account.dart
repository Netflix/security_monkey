library security_monkey.account;

import 'dart:convert';

class Account {
  int id;
  bool active;
  bool third_party;
  String name;
  String s3_name;
  String number;
  String notes;

  String toJson() {
      Map objmap = {
                  "id": id,
                  "active": active,
                  "third_party": third_party,
                  "name": name,
                  "s3_name": s3_name,
                  "number": number,
                  "notes": notes
                };
      return JSON.encode(objmap);
    }
}