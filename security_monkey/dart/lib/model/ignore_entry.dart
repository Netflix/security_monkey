library security_monkey.ignore_entry;

class IgnoreEntry {
    int id;
    String prefix;
    String notes;
    String technology;

    IgnoreEntry();

    IgnoreEntry.fromMap(Map data) {
        id = data["id"];
        prefix = data["prefix"];
        notes = data["notes"];
        technology = data["technology"];
    }
}