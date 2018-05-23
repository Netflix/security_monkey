library security_monkey.splunkalerter;

import 'dart:convert';

class SplunkAlerter {
    String id;
    String host;
    int port;
    String token;
    String sourcetype;
    String source;
    bool _log_config;
    bool _active;
    bool _changed;
    bool remove_items;

    SplunkAlerter();

    get active => _active;
    get changed => _changed;
    get log_config => _log_config;

    set log_config(logconfig) {
        _log_config = logconfig;
    }

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
        log_config = data['log_config'];
        sourcetype =  data['sourcetype'];
        source =  data['source'];
        remove_items = false;
    }

    String toJson() {
        Map objmap = {
            "id": id,
            "active": active,
            "host": host,
            "port": port,
            "token": token,
            "log_config": log_config,
            "sourcetype":sourcetype,
            "source":source
        };
        return JSON.encode(objmap);
    }
}
