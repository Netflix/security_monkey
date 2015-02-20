part of security_monkey;

@Component(
    selector: 'whitelistview',
    templateUrl: 'packages/security_monkey/component/whitelist_view_component/whitelist_view_component.html',
    //cssUrl: const ['/css/bootstrap.min.css']
    useShadowDom: false
)
class WhitelistViewComponent implements ScopeAware {
    RouteProvider routeProvider;
    Router router;
    NetworkWhitelistEntry cidr;
    bool create = false;
    bool _as_loaded = false;
    bool _is_error = false;
    String err_message = "";
    ObjectStore store;

    WhitelistViewComponent(this.routeProvider, this.router, this.store) {
        this.store = store;
        // If the URL has an ID, then let's view/edit
        if (routeProvider.parameters.containsKey("whitelistid")) {
            store.one(NetworkWhitelistEntry, routeProvider.parameters['whitelistid']).then((cidr) {
                this.cidr = cidr;
                _as_loaded = true;
            });
            create = false;
        } else {
            // If the URL does not have an ID, then let's create
            cidr = new NetworkWhitelistEntry();
            create = true;
        }
    }

    void set scope(Scope scope) {
        scope.on("globalAlert").listen(this._showMessage);
    }

    get isLoaded => create || _as_loaded;
    get isError => _is_error;

    void _showMessage(ScopeEvent event) {
        this._is_error = true;
        this.err_message = event.data;
    }

    void saveEntry() {
        if (create) {
            this.store.create(this.cidr).then((CommandResponse r) {
                int id = r.content['id'];
                router.go('viewwhitelist', {
                    'whitelistid': id
                });
            });
        } else {
            this.store.update(this.cidr).then( (_) {
                // let the page flicker so people know the update happened.
                // (poor man's UX)
                _as_loaded = false;
                store.one(NetworkWhitelistEntry, routeProvider.parameters['whitelistid']).then((cidr) {
                    this.cidr = cidr;
                    _as_loaded = true;
                });
            });
        }
    }

    void deleteEntry() {
        this.store.delete(this.cidr).then((_) {
            router.go('settings', {});
        });
    }

}
