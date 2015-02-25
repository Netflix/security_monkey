library security_monkey.model_revision;

import 'dart:convert';
import 'RevisionComment.dart';
import 'Item.dart';
import 'package:security_monkey/util/utils.dart' show localDateFromAPIDate;
import 'package:aws_policy_expander_minimizer/aws_policy_expander_minimizer.dart';

class Revision {
    int id;
    int item_id;
    bool active;
    //String date_created;
    DateTime date_created;
    String diff_html;
    Item item;
    List<RevisionComment> comments;
    Expander expander = new Expander();
    var encoder = new JsonEncoder.withIndent("  ");
    var _expanded = null;

    bool has_expanded() {
      if (_expanded == "exception") {
        return false;
      }

      if (_expanded != null) {
        return true;
      }

      try {
        _expanded = expander.expandPolicies(_config);
        return true;
      } catch (_) {
        _expanded = "exception";
        return false;
      }
    }

    get expanded {
      if (_expanded == "exception") {
        return config;
      }

      if (_expanded != null) {
        return encoder.convert(_expanded);
      }

      try {
        _expanded = expander.expandPolicies(_config);
        return encoder.convert(_expanded);
      } catch (_) {
        _expanded = "exception";
        return config;
      }
    }

    var _config;
    get config {
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
            date_created = localDateFromAPIDate(data['date_created']);
        }

        if (data.containsKey('config')) {
            config = data['config'];
        }

        comments = new List<RevisionComment>();
        if (data.containsKey('comments')) {
            for (var comment in data['comments']) {
                comments.add(new RevisionComment.fromMap(comment));
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
            date_created = localDateFromAPIDate(data['date_created']);
        }

        if (data.containsKey('config')) {
            config = data['config'];
        }

        comments = new List<RevisionComment>();
        if (data.containsKey('comments')) {
            for (var comment in data['comments']) {
                comments.add(new RevisionComment.fromMap(comment));
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
