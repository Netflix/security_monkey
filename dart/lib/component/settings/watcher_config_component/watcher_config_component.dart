part of security_monkey;

@Component(
  selector: 'watcher-config-cmp',
  templateUrl: 'packages/security_monkey/component/settings/watcher_config_component/watcher_config_component.html',
  useShadowDom: false
)

class WatcherConfigComponent extends PaginatedTable {
    UsernameService us;
    ObjectStore store;
    List<WatcherConfig> configs;

    WatcherConfigComponent(this.store) {
        this.store = store;
        this.list();
    }

    void list() {
        configs = new List<WatcherConfigs>();
        store.list(WatcherConfig, params: {
                "count": ipp_as_int,
                "page": currentPage
            }).then((config_response) {
            super.setPaginationData(config_response.meta);
            this.configs = config_response;
            super.is_loaded = true;
        });
    }

    void updateSetting(WatcherConfig config) {
        this.store.update(config).then((_) {
            list();
        });
    }

    get isLoaded => super.is_loaded;
    get isError => super.is_error;
}
