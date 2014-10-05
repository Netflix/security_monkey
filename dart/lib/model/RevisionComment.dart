library security_monkey.revision_comment;

import 'package:security_monkey/util/utils.dart' show localDateFromAPIDate;

/// Format from API:
/// {
///     "date_created": "2014-05-07 16:25:50",
///     "id": 2,
///     "revision_id": 2405,
///     "text": "second comment",
///     "user": "user@example.com"
/// }

class RevisionComment {
    int id;
    int revision_id;
    String text;
    String user;
    DateTime date_created;

    RevisionComment(Map<String, Object> data) {
        id = data['id'];
        revision_id = data['revision_id'];
        text = data['text'];
        user = data['user'];
        date_created = localDateFromAPIDate(data['date_created']);
    }
}
