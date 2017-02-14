library security_monkey.network_whitelist_entry;

import 'dart:convert';

class NetworkWhitelistEntry {
    int id;
    String name;
    String cidr;
    String notes;

    NetworkWhitelistEntry();

    NetworkWhitelistEntry.fromMap(Map data) {
        id = data["id"];
        name = data["name"];
        notes = data["notes"];
        cidr = data["cidr"];
    }

    Map toMap() {
        return {
            "id": id,
            "name": name,
            "cidr": cidr,
            "notes": notes
        };
    }

}
