library security_monkey.custom_field_config;

class CustomFieldConfig {
    String name;
    String label;
    bool editable;
    String tool_tip;
    bool password;
    List<String> allowed_values;

    CustomFieldConfig.fromMap(Map data) {
        name = data['name'];
        label = data['label'];
        editable = data['editable'];
        tool_tip = data['tool_tip'];
        password = data['password'];
        allowed_values = data['allowed_values'];
    }
}
