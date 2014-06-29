library security_monkey.user_setting;

import 'package:SecurityMonkey/model/Account.dart';
import 'dart:convert';

class UserSetting {

  List<Account> accounts = new List<Account>();
  bool daily_audit_email = false;
  String change_report_setting = "NONE";

  List<int> account_ids() {
    List<int> account_ids = new List<int>();
    for (Account account in accounts) {
      account_ids.add(account.id);
    }
    return account_ids;
  }

  String toJson() {
    Map objmap = {
                "accounts": account_ids(),
                "daily_audit_email": daily_audit_email,
                "change_report_setting": change_report_setting
              };
    return JSON.encode(objmap);
  }

}