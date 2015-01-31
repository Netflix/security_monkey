library security_monkey.auditorsetting;

class AuditorSetting {
    String account;
    String technology;
    String issue;
    int count;
    bool disabled;
    int id;

    AuditorSetting();

    AuditorSetting.fromMap(Map data) {
        account = data["account_name"];
        issue = data["issue"];
        count = data["count"];
        technology = data["tech_name"];
        disabled = data["disabled"];
        id = data["id"];
    }
}
