part of security_monkey;
// TODO : SplunkAlerter
@Component(
    selector: 'splunkalerterview',
    templateUrl: 'packages/security_monkey/component/splunk_alerter_view_component/splunk_alerter_view_component.html',
    //cssUrl: const ['/css/bootstrap.min.css'],
    useShadowDom: false
)
class SplunkAlerterViewComponent implements ScopeAware {
    RouteProvider routeProvider;
    Router router;
    SplunkAlerter splunkalerter;
    bool create = false;
    bool _as_loaded = false;

    bool _is_error = false;
    String err_message = "";

    ObjectStore store;

    SplunkAlerterViewComponent(this.routeProvider, this.router, this.store) {
        this.store = store;
        // If the URL has an ID, then let's view/edit
        if (routeProvider.parameters.containsKey("alerterid")) {
            store.one(SplunkAlerter, routeProvider.parameters['alerterid']).then((alerter) {
                this.splunkalerter = alerter;
                this._as_loaded = true;
            });
            create = false;
        } else {
            // If the URL does not have an ID, then let's create
            this.splunkalerter = new SplunkAlerter();
            this._as_loaded = true;
            this.create = true;
        }
    }

    void set scope(Scope scope) {
        scope.on("globalAlert").listen(this._showMessage);
    }

    get isLoaded => _as_loaded;
    get isError => _is_error;

    void _showMessage(ScopeEvent event) {
        this._is_error = true;
        this.err_message = event.data;
    }

    void saveAlerter() {
        if (create) {
            this.store.create(this.splunkalerter).then((CommandResponse r) {
                int id = r.content['id'];
                router.go('viewsplunkalerter', {
                    'alerterid': id
                });
            });
        } else {
            this.store.update(this.splunkalerter).then((_) {
                window.location.reload();
            });
        }
    }

    void deleteAlerter() {
        this.store.delete(this.splunkalerter).then((_) {
            router.go('settings', {});
        });
    }

}
