library security_monkey.account_config;

import 'custom_field_config.dart';

class AccountConfig {
    List<String> account_types = new List<String>();
    Map<String, String> identifier_labels = new Map<String, String>();
    Map<String, String> identifier_tool_tips = new Map<String, String>();
    Map<String, List<CustomFieldConfig>> fields = new Map<String, List<CustomFieldConfig>>();

    AccountConfig();

    AccountConfig.fromMap(Map data) {
        if (data.containsKey('custom_configs')) {
            var acc_configs = data['custom_configs'];
            acc_configs.forEach((k,v) => this._addToLists(k, v));
        }
    }

    void _addToLists(account_type, values) {
        this.account_types.add(account_type);
        this.identifier_labels[account_type] = values['identifier_label'];
        this.identifier_tool_tips[account_type] = values['identifier_tool_tip'];

        var list = new List<CustomFieldConfig>();
        var field_config = values['fields'];
        for (var field in field_config) {
            list.add(new CustomFieldConfig.fromMap(field));
        }
        this.fields[account_type] = list;
    }
}
