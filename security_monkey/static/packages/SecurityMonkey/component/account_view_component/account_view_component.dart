library security_monkey.account_view_component;

import 'package:angular/angular.dart';
import 'package:SecurityMonkey/service/account_service.dart';
import 'package:SecurityMonkey/model/Account.dart';

@Component(
    selector: 'accountview',
    templateUrl: 'packages/SecurityMonkey/component/account_view_component/account_view_component.html',
    cssUrl: const ['css/bootstrap.min.css'],
    publishAs: 'cmp')
class AccountViewComponent {
  AccountService as;
  RouteProvider routeProvider;
  Router router;
  Account account;
  bool create = false;

  AccountViewComponent(this.as, this.routeProvider, this.router) {
    /* If the URL has an ID, then let's view/edit */
    if (routeProvider.parameters.containsKey("accountid")) {
      this.as.getAccount(routeProvider.parameters['accountid'])
        .then((Account account) {
        this.account = account;
      });
      create = false;
    } else {
      /* If the URL does not have an ID, then let's create */
      account = new Account();
      create = true;
    }
  }

  get isLoaded => create || as.isLoaded;
  get isError => as.isError;

  void saveAccount() {
    if (create) {
      as.createAccount(account).then((Account account) {
        int id = account.id;
        router.go('viewaccount', {'accountid':id});
      });
    } else {
      as.saveAccount(account);
    }
  }

// Users can just make an account inactive.
// Not sure if we should expose delete.
  void deleteAccount() {
    as.deleteAccount(account.id).then((Account account) {
      router.go('settings', {});
    });
  }

}