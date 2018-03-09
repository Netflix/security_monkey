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
        account = data["account"];
        issue = data["issue"];
        count = data["count"];
        technology = data["technology"];
        disabled = data["disabled"];
        id = data["id"];
    }
}
