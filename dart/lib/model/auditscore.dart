library security_monkey.auditscore;

class AuditScore {
    String method;
    String technology;
    int score;
    int id;
    bool disabled;

    List<AccountPatternAuditScore> account_pattern_scores = new List<AccountPatternAuditScore>();

    AuditScore();

    AuditScore.fromMap(Map data) {
        method = data["method"];
        score = data["score"];
        technology = data["technology"];
        id = data["id"];
        disabled = data["disabled"];
        account_pattern_scores = data["account_pattern_scores"];
    }

    String toJson() {
        Map objmap = {
            "id": id,
            "method": method,
            "technology": technology,
            "notes": notes,
            "disabled": disabled
        };
        return JSON.encode(objmap);
    }

}
