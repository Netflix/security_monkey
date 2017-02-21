library security_monkey.account_pattern_audit_score;

class AccountPatternAuditScore {
    int id;
    String account_type;
    String account_field;
    String account_pattern;
    int score;
    int itemauditscores_id;

    AccountPatternAuditScore();

    AccountPatternAuditScore.fromMap(Map data) {
        id = data["id"];
        account_type = data["account_type"];
        account_field = data["account_field"];
        account_pattern = data["account_pattern"];
        score = data["score"];
        itemauditscores_id = data["itemauditscores_id"];
    }

    String toJson() {
        Map objmap = {
            "id": id,
            "account_type": account_type,
            "account_field": account_field,
            "account_pattern": account_pattern,
            "score": score,
            "itemauditscores_id": itemauditscores_id
        };
        return JSON.encode(objmap);
    }

}
