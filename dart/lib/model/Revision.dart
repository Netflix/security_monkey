library security_monkey.model_revision;

import 'dart:convert';
import 'package:SecurityMonkey/model/RevisionComment.dart';
import 'package:SecurityMonkey/model/Item.dart';

class Revision {
    int id;
    int item_id;
    bool active;
    //String date_created;
    DateTime date_created;
    String diff_html;
    Item item;
    List<RevisionComment> comments;
    var _config;
    get config {
        var encoder = new JsonEncoder.withIndent("     ");
        return encoder.convert(_config);
    }
    set config(c) {
        _config = c;
    }

    Revision.fromItem(Map<String, Object> data, item) {
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
    }

    Revision.fromMap(Map<String, Object> data) {
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

        item = new Item.fromMap({
            "item": data
        });
    }
}
