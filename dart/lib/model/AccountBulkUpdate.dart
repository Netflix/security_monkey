library security_monkey.account_bulk_update;

import 'Account.dart';
import 'dart:convert';

class AccountBulkUpdate {
    Map<List> accounts_map = new Map<List>();

    AccountBulkUpdate();

    AccountBulkUpdate.fromAccountList(List<Account> accounts) {
        for (var account in accounts) {
            this.accounts_map[account.name] = account.active;
        }
    }

    String toJson() {
        return JSON.encode(this.accounts_map);
    }
}
