part of security_monkey;

@Component(
  selector: 'splunk-alerter-config-cmp',
  templateUrl: 'packages/security_monkey/component/settings/splunk_alerter_config_component/splunk_alerter_config_component.html',
  useShadowDom: false
)

class SplunkAlerterConfigComponent extends PaginatedTable {
    UsernameService us;
    Router router;
    ObjectStore store;
    List<SplunkAlerter> configs;

    SplunkAlerterConfigComponent(this.router, this.store, this.us) {
        this.store = store;
        this.list();
    }

    void list() {
        configs = new List<SplunkAlerter>();
        store.list(SplunkAlerter, params: {
                "count": ipp_as_int,
                "page": currentPage
            }).then((config_response) {
            super.setPaginationData(config_response.meta);
            this.configs = config_response;
            super.is_loaded = true;
        });
    }

    void delete(SplunkAlerter alerter) {
         this.store.delete(alerter).then((_) {
            list();
        });
    }

    void createSplunkAlerter() {
        router.go('createsplunkalerter', {});
    }

    void setActive(SplunkAlerter alerter, bool enable) {
        alerter.active = enable;
        this.store.update(alerter).then((_) {
            list();
        });
    }

    void setLogConfig(SplunkAlerter alerter, bool enable) {
        alerter.log_config = enable;
        this.store.update(alerter).then((_) {
            list();
        });
    }

    void edit(SplunkAlerter alerter) {
         router.go('viewsplunkalerter', {
                    'alerterid': alerter.id
         });
    }

    get isLoaded => super.is_loaded;
    get isError => super.is_error;
}
