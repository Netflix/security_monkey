library security_monkey.revision;

import 'dart:convert';
import 'package:SecurityMonkey/model/RevisionComment.dart';

class Revision {
  int id;
  int item_id;
  var _config;
  get config => JSON.encode(_config);
  set config(c) {
    _config = c;
  }

  bool active;
  //String date_created;
  DateTime date_created;

  // From the parent item
  String account;
  String technology;
  String name;
  String region;
  String diff_html;
  List<RevisionComment> comments;

  Revision(Map<String, Object> data) {

    id = data['id'];
    item_id = data['item_id'];
    active = data['active'];
    if (data.containsKey('date_created')) {
      date_created = DateTime.parse(data['date_created']);
    }

    if (data.containsKey('config')) {
      config = data['config'];
    }

    comments = new List<RevisionComment>();
    if (data.containsKey('comments')) {
      for (var comment in data['comments']) {
        comments.add(new RevisionComment(comment));
      }
    }

    if (data.containsKey('diff_html')) {
      diff_html = data['diff_html'];
    }

    // From parent Item.
    // Should be refactored elsewhere.
    if (data.containsKey('name')) {
      name = data['name'];
      // If it has name, assume it has these others
      account = data['account'];
      technology = data['technology'];
      region = data['region'];
    }
  }
}