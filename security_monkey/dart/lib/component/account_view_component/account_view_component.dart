part of security_monkey;

@Component(
    selector: 'accountview',
    templateUrl: 'packages/security_monkey/component/account_view_component/account_view_component.html',
    //cssUrl: const ['/css/bootstrap.min.css'],
    useShadowDom: false
)
class AccountViewComponent implements ScopeAware {
    RouteProvider routeProvider;
    Router router;
    Account account;
    bool create = false;
    bool _as_loaded = false;
    bool _cfg_loaded = false;
    bool _is_error = false;
    String err_message = "";
    AccountConfig config;
    ObjectStore store;

    AccountViewComponent(this.routeProvider, this.router, this.store) {
        this.store = store;
        // If the URL has an ID, then let's view/edit
        if (routeProvider.parameters.containsKey("accountid")) {
            store.one(Account, routeProvider.parameters['accountid']).then((account) {
                this.account = account;
                this._as_loaded = true;
            });
            store.one(AccountConfig, "custom").then((account_config) {
                this.config = account_config;
                _cfg_loaded = true;
            });
            create = false;
        } else {
            // If the URL does not have an ID, then let's create
            this.account = new Account();
            store.one(AccountConfig, "custom").then((account_config) {
                this.config = account_config;
                _cfg_loaded = true;
            });
            _as_loaded = true;
            create = true;
        }
    }

    void set scope(Scope scope) {
        scope.on("globalAlert").listen(this._showMessage);
    }

    get isLoaded => _as_loaded && _cfg_loaded;
    get isError => _is_error;

    void _showMessage(ScopeEvent event) {
        this._is_error = true;
        this.err_message = event.data;
    }

    void saveAccount() {
        if (create) {
            this.store.create(this.account).then((CommandResponse r) {
                int id = r.content['id'];
                router.go('viewaccount', {
                    'accountid': id
                });
            });
        } else {
            this.store.update(this.account).then((_) {
                window.location.reload();
            });
        }
    }

    /// Users can just make an account inactive.
    /// Not sure if we should expose delete.
    void deleteAccount() {
        this.store.delete(this.account).then((_) {
            router.go('settings', {});
        });
    }

}
