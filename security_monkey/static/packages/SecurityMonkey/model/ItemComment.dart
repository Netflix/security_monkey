library security_monkey.item_comment;
/*
{
    "date_created": "2014-05-07 16:25:50",
    "id": 2,
    "revision_id": 2405,
    "text": "second comment",
    "user": "user@example.com"
}
*/

class ItemComment {
  int id;
  int item_id;
  String text;
  String user;
  DateTime date_created;

  ItemComment(Map<String, Object> data) {
    id = data['id'];
    item_id = data['revision_id'];
    text = data['text'];
    user = data['user'];
    date_created = DateTime.parse(data['date_created']);
  }
}

