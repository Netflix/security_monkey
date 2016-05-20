library security_monkey.account;

import 'dart:convert';

class Account {
    int id;
    String name;
    String identifier;
    String notes;
    bool _active;
    bool _third_party;
    String account_type;
    Map<String, String> custom_field_values = new Map<String, String>();

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
        identifier = data['identifier'];
        notes = data['notes'];
        account_type = data['account_type'];

        if (data.containsKey('custom_fields')) {
            for (var field in data['custom_fields']) {
                custom_field_values[field['name']] = field['value'];
            }
        }
    }

    String toJson() {
        Map objmap = {
            "id": id,
            "active": active,
            "third_party": third_party,
            "name": name,
            "identifier": identifier,
            "notes": notes,
            "account_type": account_type,
            "custom_fields": custom_field_values
        };
        return JSON.encode(objmap);
    }
}
