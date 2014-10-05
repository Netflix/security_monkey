library security_monkey.user_setting;

import 'Account.dart';
import 'dart:convert';

class UserSetting {

    List<Account> accounts = new List<Account>();
    bool daily_audit_email = false;
    String change_report_setting = "NONE";

    get account_ids => accounts.map((account) => account.id);

    String toJson() {
        Map objmap = {
            "accounts": account_ids(),
            "daily_audit_email": daily_audit_email,
            "change_report_setting": change_report_setting
        };
        return JSON.encode(objmap);
    }

}
