part of security_monkey;

@Component(
    selector: 'accountpatternauditscoreview',
    templateUrl: 'packages/security_monkey/component/account_pattern_audit_score_view_component/account_pattern_audit_score_view_component.html',
    useShadowDom: false
)
class AccountPatternAuditScoreComponent implements ScopeAware {
    RouteProvider routeProvider;
    Router router;
    AccountPatternAuditScore accountpatternauditscore;
    bool create = false;
    bool _as_loaded = false;
    bool _is_error = false;
    bool _cfg_loaded = false;
    String err_message = "";
    ObjectStore store;
    UsernameService us;
    AccountConfig config;

    AccountPatternAuditScoreComponent(this.routeProvider, this.router, this.store, this.us) {
        this.store = store;
        // If the URL has an ID, then let's view/edit
        if (routeProvider.parameters.containsKey("accountpatternauditscoreid")) {
            store.one(AccountPatternAuditScore, routeProvider.parameters['accountpatternauditscoreid']).then((accountpatternauditscore) {
                this.accountpatternauditscore = accountpatternauditscore;
                _as_loaded = true;
            });
            create = false;
        } else {
            // If the URL does not have an ID, then let's create
            this.accountpatternauditscore = new AccountPatternAuditScore();
            this.accountpatternauditscore.itemauditscores_id = routeProvider.parameters['auditscoreid'];
            create = true;
        }
        store.one(AccountConfig, "all").then((account_config) {
            this.config = account_config;

            _cfg_loaded = true;
        });
    }

    void set scope(Scope scope) {
        scope.on("globalAlert").listen(this._showMessage);
    }

    get isLoaded => (create || _as_loaded) && _cfg_loaded;
    get isError => _is_error;

    void _showMessage(ScopeEvent event) {
        this._is_error = true;
        this.err_message = event.data;
    }

    void saveEntry() {
        if (create) {
            this.store.create(this.accountpatternauditscore).then((CommandResponse r) {
                int id = r.content['id'];
                router.go('viewaccountpatternauditscore', {
                    'accountpatternauditscoreid': id
                });
            });
        } else {
            this.store.update(this.accountpatternauditscore).then( (_) {
                // let the page flicker so people know the update happened.
                // (poor man's UX)
                _as_loaded = false;
                store.one(AccountPatternAuditScore, routeProvider.parameters['accountpatternauditscoreid']).then((accountpatternauditscore) {
                    this.accountpatternauditscore = accountpatternauditscore;
                    _as_loaded = true;
                });
            });
        }
    }

    void deleteEntry() {
        this.store.delete(this.accountpatternauditscore).then((_) {
            router.go('viewauditscore', {
                'auditscoreid': routeProvider.parameters['auditscoreid']
            });
        });
    }

    int getAllowedValues() {
        if (accountpatternauditscore.account_type != null && accountpatternauditscore.account_field != null) {
            List<CustomFieldConfig> field_configs = this.config.fields[accountpatternauditscore.account_type];
            for (var field_config in field_configs) {
                if (field_config.name == accountpatternauditscore.account_field) {
                    return field_config.allowed_values;
                }
            }
        }

        return null;
    }
}
