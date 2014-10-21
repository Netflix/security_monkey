part of security_monkey;

@Component(
    selector: 'ignoreentryview',
    templateUrl: 'packages/security_monkey/component/ignore_entry_component/ignore_entry_component.html',
    cssUrl: const ['css/bootstrap.min.css'],
    publishAs: 'cmp')
class IgnoreEntryComponent {
    RouteProvider routeProvider;
    Router router;
    IgnoreEntry ignoreentry;
    bool create = false;
    bool _as_loaded = false;
    bool _is_error = false;
    String err_message = "";
    ObjectStore store;
    Scope scope;

    IgnoreEntryComponent(this.routeProvider, this.router, this.store, this.scope) {
        print("Inside IgnoreEntryComponent Constructor.");
        scope.on("globalAlert").listen(this._showMessage);

        this.store = store;
        // If the URL has an ID, then let's view/edit
        if (routeProvider.parameters.containsKey("ignoreentryid")) {
            store.one(IgnoreEntry, routeProvider.parameters['ignoreentryid']).then((ignoreentry) {
                this.ignoreentry = ignoreentry;
                _as_loaded = true;
            });
            create = false;
        } else {
            // If the URL does not have an ID, then let's create
            ignoreentry = new IgnoreEntry();
            create = true;
        }
    }

    get isLoaded => create || _as_loaded;
    get isError => _is_error;

    void _showMessage(ScopeEvent event) {
        this._is_error = true;
        this.err_message = event.data;
    }

    void saveEntry() {
        if (create) {
            this.store.create(this.ignoreentry).then((CommandResponse r) {
                int id = r.content['id'];
                router.go('viewignoreentry', {
                    'ignoreentryid': id
                });
            });
        } else {
            print("ID: ${this.ignoreentry.id}");
            this.store.update(this.ignoreentry).then( (_) {
                // let the page flicker so people know the update happened.
                // (poor man's UX)
                _as_loaded = false;
                store.one(IgnoreEntry, routeProvider.parameters['ignoreentryid']).then((ignoreentry) {
                    this.ignoreentry = ignoreentry;
                    _as_loaded = true;
                });
            });

        }
    }

    void deleteEntry() {
        this.store.delete(this.ignoreentry).then((_) {
            router.go('settings', {});
        });
    }

}
