library security_monkey.network_whitelist_entry;

import 'dart:convert';

class NetworkWhitelistEntry {
  int id;
  String name;
  String network_address;
  int network_mask;
  String _cidr;
  String notes;
  
  get cidr => network_address + "/" + network_mask.toString();
  set cidr (String new_cidr) {
    _cidr = new_cidr;
    if(new_cidr.contains('/')) {
      network_address = new_cidr.split('/')[0];
      network_mask = int.parse(new_cidr.split('/')[1]);
    } else {
      print("Given bad CIDR: $new_cidr.  Should be in format 10.0.0.0/8.");
    }
  }
  
  String toJson() {
    Map objmap = {
      "id": id,
      "name": name,
      "cidr": cidr,
      "notes": notes
    };
    return JSON.encode(objmap);
  }
}