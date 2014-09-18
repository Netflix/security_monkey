library security_monkey.settings_component;

import 'package:angular/angular.dart';
import 'package:SecurityMonkey/service/user_settings_service.dart';
import 'package:SecurityMonkey/model/Account.dart';
import 'package:SecurityMonkey/model/network_whitelist_entry.dart';
import 'package:SecurityMonkey/component/paginated_table/paginated_table.dart';
import 'package:hammock/hammock.dart';

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

  SettingsComponent(this.uss, this.router, this.store, this.scope) {
    super.setupTable(scope);
    scope.on("accounts-pagination").listen(super.setPaginationData);
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