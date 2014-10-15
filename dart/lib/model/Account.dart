library security_monkey.account;

import 'dart:convert';

class Account {
    int id;
    String name;
    String s3_name;
    String number;
    String notes;
    bool _active;
    bool _third_party;

    Account();

    get active => _active;
    get third_party => _third_party;

    set active(active) {
        if (active) {
            _third_party = false;
        }
        _active = active;
    }

    set third_party(third_party) {
        if (third_party) {
            _active = false;
        }
        _third_party = third_party;
    }

    Account.fromMap(Map data) {
        id = data['id'];
        active = data['active'];
        third_party = data['third_party'];
        name = data['name'];
        s3_name = data['s3_name'];
        number = data['number'];
        notes = data['notes'];
    }

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
