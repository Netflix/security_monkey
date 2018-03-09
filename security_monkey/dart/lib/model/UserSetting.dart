library security_monkey.user_setting;

import 'Account.dart';
import 'dart:convert';

class UserSetting {

    List<Account> accounts = new List<Account>();
    bool daily_audit_email = false;
    String change_report_setting = "NONE";
    int id;

    get account_ids => accounts.map((account) => account.id).toList();

    UserSetting.fromMap(Map setting) {

        print("UserSetting Constructor Received $setting");
        if (setting.containsKey("settings")) {
            setting = setting["settings"][0];
        }


        daily_audit_email = setting['daily_audit_email'];
        change_report_setting = setting['change_reports'];
        for (var account_id in setting['accounts']) {
          Account account = new Account()
            ..id = account_id;
          accounts.add(account);
        }
    }

    String toJson() {
        Map objmap = {
            "accounts": account_ids,
            "daily_audit_email": daily_audit_email,
            "change_report_setting": change_report_setting
        };
        return JSON.encode(objmap);
    }

}
