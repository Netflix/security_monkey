part of security_monkey;

@Component(
    selector: 'auditscoreview',
    templateUrl: 'packages/security_monkey/component/auditscore_view_component/auditscore_view_component.html',
    //cssUrl: const ['/css/bootstrap.min.css']
    useShadowDom: false
)
class AuditScoreComponent implements ScopeAware {
    RouteProvider routeProvider;
    Router router;
    AuditScore auditscore;
    List<String> technologies;
    Map<String, List<String>> methods;
    bool create = false;
    bool _as_loaded = false;
    bool _is_error = false;
    String err_message = "";
    ObjectStore store;
    UsernameService us;

    AuditScoreComponent(this.routeProvider, this.router, this.store, this.us) {
        this.store = store;
        // If the URL has an ID, then let's view/edit
        if (routeProvider.parameters.containsKey("auditscoreid")) {
            store.one(AuditScore, routeProvider.parameters['auditscoreid']).then((auditscore) {
                this.auditscore = auditscore;
                _as_loaded = true;
            });
            create = false;
        } else {
            // If the URL does not have an ID, then let's create
            auditscore = new AuditScore();
            create = true;
        }
        store.one(TechMethods, "all").then((techmethods) {
          this.technologies = techmethods.technologies;
          this.methods = techmethods.methods;
        });

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
            this.store.create(this.auditscore).then((CommandResponse r) {
                int id = r.content['id'];
                router.go('viewauditscore', {
                    'auditscoreid': id
                });
            });
        } else {
            this.store.update(this.auditscore).then( (_) {
                // let the page flicker so people know the update happened.
                // (poor man's UX)
                _as_loaded = false;
                store.one(AuditScore, routeProvider.parameters['auditscoreid']).then((auditscore) {
                    this.auditscore = auditscore;
                    _as_loaded = true;
                });
            });
        }
    }

    void deleteEntry() {
        this.store.delete(this.auditscore).then((_) {
            router.go('settings', {});
        });
    }

    void createAccountPatternAuditScore() {
        router.go('createaccountpatternauditscore', {
            'auditscoreid': routeProvider.parameters['auditscoreid']
        });
    }

    void reload() {
        _as_loaded = false;
        _as_loaded = true;
    }
}
