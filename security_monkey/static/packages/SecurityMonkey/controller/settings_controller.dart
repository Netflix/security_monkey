library security_monkey.settings_controller;

import 'package:angular/angular.dart';
import 'package:SecurityMonkey/service/account_service.dart';
import 'package:SecurityMonkey/service/user_settings_service.dart';
import 'package:SecurityMonkey/model/Account.dart';

@Controller(
    selector: '[settings]',
    publishAs: 'cmp')
class SettingsController {
  AccountService as;
  UserSettingsService uss;
  Router router;
  List<Account> accounts;

  SettingsController(this.as, this.uss, this.router) {
    this.as.listAccounts().then((List<Account> new_accounts) {
      this.accounts = new_accounts;
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
    print("Inside toggle");
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
        print("adding");
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
  get isLoaded => uss.isLoaded && as.isLoaded;
  get isError => uss.isError || as.isError;

}