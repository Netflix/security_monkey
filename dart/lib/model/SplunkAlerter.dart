library security_monkey.splunkalerter;

import 'dart:convert';

class SplunkAlerter {
    int id;
    String host;
    int port;
    String token;
    bool _active;
    bool _changed;
    bool remove_items;

    SplunkAlerter();

    get active => _active;
    get changed => _changed;

    set active(active) {
        _active = active;
    }

    set changed(changed) {
        _changed = changed;
    }

    SplunkAlerter.fromMap(Map data) {
        id = data['id'];
        host = data['host'];
        port = data['port'];
        token = data['token'];
        active = data['active'];
        remove_items = false;
    }

    String toJson() {
        Map objmap = {
            "id": id,
            "active": active,
            "host": host,
            "port": port,
            "token": token
        };
        return JSON.encode(objmap);
    }
}
