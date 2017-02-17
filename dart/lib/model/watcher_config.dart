library security_monkey.watcher_config;

class WatcherConfig {
    int id;
    String index;
    String interval;
    bool active;
    bool remove_items;
    bool changed;

    WatcherConfig();

    WatcherConfig.fromMap(Map data) {
        id = data["id"];
        index = data["index"];
        interval = data["interval"];
        active = data["active"];
        remove_items = false;
    }
}
