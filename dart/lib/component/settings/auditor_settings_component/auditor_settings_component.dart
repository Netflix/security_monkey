part of security_monkey;

@Component(
    selector: 'auditor-settings-cmp',
    templateUrl: 'packages/security_monkey/component/settings/auditor_settings_component/auditor_settings_component.html',
    useShadowDom: false
)
class AuditorSettingsComponent extends PaginatedTable {
    Router router;
    List<AuditorSetting> auditorlist;
    ObjectStore store;
    final Http _http;

    get isLoaded => super.is_loaded;
    get isError => super.is_error;

    String url_encode(input) => param_to_url(input);

    void toggleAuditorEnable(auditor) {
        auditor.disabled = !auditor.disabled;
        store.update(auditor);
    }

    AuditorSettingsComponent(this.router, this.store, this._http) {
        list();
    }

    void list() {
        super.is_loaded = false;
        store.list(AuditorSetting, params: {
            "count": ipp_as_int,
            "page": currentPage,
            "order_by": sorting_column,
            "order_dir": order_dir()
        }).then((auditor_settings) {
            super.setPaginationData(auditor_settings.meta);
            this.auditorlist = auditor_settings;
            super.is_loaded = true;
        });
    }
}