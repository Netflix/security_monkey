part of security_monkey;

@Component(
    selector: 'settings-cmp',
    templateUrl: 'packages/SecurityMonkey/component/settings_component/settings_component.html',
    cssUrl: const ['css/bootstrap.min.css'],
    publishAs: 'cmp')
class SettingsComponent extends PaginatedTable {
  UserSettingsService uss;
  Router router;
  List<Account> accounts;
  List<NetworkWhitelistEntry> cidrs;
  Scope scope;
  ObjectStore store;

  SettingsComponent(this.uss, this.router, this.store, Scope scope)
      : this.scope=scope,
      super(scope)
      {
    cidrs = new List<NetworkWhitelistEntry>();
    accounts = new List<Account>();
    list();
  }

  void list() {
    store.list(Account,
      params: {
          "count": ipp_as_int,
          "page": currentPage
      }).then((accounts) {
          super.setPaginationData(accounts.meta);
          this.accounts = accounts;
          super.is_loaded = true;
    });
  }

  bool enabledValueForAccount(bool active, bool third_party) {
    return active && (third_party == false);
  }

  bool notificationValueForAccount(var id) {
    for (Account account in user_setting.accounts) {
      if( account.id == id ) {
        return true;
      }
    }
    return false;
  }

  void toggleNotificationForAccount(var id) {
    // Remove existing accounts.
    for (Account account in user_setting.accounts) {
      if( account.id == id ) {
        user_setting.accounts.remove(account);
        print("removing");
        return;
      }
    }

    // Add new accounts
    for (Account account in this.accounts) {
      if(account.id == id) {
        user_setting.accounts.add(account);
        return;
      }
    }
  }

  void saveSettings() {
    uss.saveSettings().then((_) {
      print("Save Settings Complete!");
    });
  }

  void createAccount() {
    router.go('createaccount', {});
  }

  get user_setting => uss.user_setting;
  get isLoaded => uss.isLoaded && super.is_loaded;
  get isError => uss.isError || super.is_error;
}