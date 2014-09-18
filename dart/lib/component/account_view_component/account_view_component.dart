//library security_monkey.account_view_component;
part of security_monkey;

@Component(
    selector: 'accountview',
    templateUrl: 'packages/SecurityMonkey/component/account_view_component/account_view_component.html',
    cssUrl: const ['css/bootstrap.min.css'],
    publishAs: 'cmp')
class AccountViewComponent {
  RouteProvider routeProvider;
  Router router;
  Account account;
  bool create = false;
  bool _as_loaded = false;
  bool _is_error = false;
  String err_message = "";
  ObjectStore store;
  Scope scope;

  AccountViewComponent(this.routeProvider, this.router, this.store, this.scope) {
    scope.on("globalAlert").listen(this._showMessage);

    this.store = store;
    /* If the URL has an ID, then let's view/edit */
    if (routeProvider.parameters.containsKey("accountid")) {
      store.one(Account, routeProvider.parameters['accountid'])
      .then((Account account) {
          this.account = account;
          _as_loaded = true;
      });
      create = false;
    } else {
      // If the URL does not have an ID, then let's create
      account = new Account();
      create = true;
    }
  }

  get isLoaded => create || _as_loaded;
  get isError => _is_error;

  void _showMessage(ScopeEvent event) {
    this._is_error = true;
    this.err_message = event.data;
  }

  void saveAccount() {
    if (create) {
        this.store.create(this.account).then((CommandResponse r) {
          int id = r.content['id'];
          router.go('viewaccount', {'accountid':id});
        });
    } else {
        this.store.update(this.account);
    }
  }

// Users can just make an account inactive.
// Not sure if we should expose delete.
  void deleteAccount() {
      this.store.delete(this.account).then((_) {
          router.go('settings', {});
      });
  }

}