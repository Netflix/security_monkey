library security_monkey.auditscore;

class AuditScore {
    String method;
    String technology;
    int score;
    int id;

    AuditScore();

    AuditScore.fromMap(Map data) {
        method = data["method"];
        score = data["score"];
        technology = data["technology"];
        id = data["id"];
    }

    String toJson() {
        Map objmap = {
            "id": id,
            "method": method,
            "technology": technology,
            "notes": notes
        };
        return JSON.encode(objmap);
    }

}
