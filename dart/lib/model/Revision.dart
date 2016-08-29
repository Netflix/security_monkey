library security_monkey.model_revision;

import 'dart:convert';
import 'RevisionComment.dart';
import 'CloudTrail.dart';
import 'Item.dart';
import 'package:security_monkey/util/utils.dart' show localDateFromAPIDate;
import 'package:aws_policy_expander_minimizer/aws_policy_expander_minimizer.dart';

class Revision {
    int id;
    int item_id;
    bool active;
    //String date_created;
    DateTime date_created;
    DateTime date_last_ephemeral_change;
    String diff_html;
    Item item;
    List<RevisionComment> comments;
    List<CloudTrail> cloudtrail_entries;
    Expander expander = new Expander();
    Minimizer minimizer = new Minimizer();
    var encoder = new JsonEncoder.withIndent("  ");
    var _expanded = null;
    var _minimized = null;
    var _minchars = 5;

    bool selected_for_action = false;

    bool has_minimized(int minChars) {
      if (_minimized == "exception") {
        return false;
      }

      if (_minimized != null && _minchars == minChars) {
        return true;
      }

      try {
        _minimized = minimizer.minimizePolicies(_config, minChars);
        return true;
      } catch (_) {
        _minimized = "exception";
        return false;
      }
    }

    dynamic minimized(int minChars) {
      if (_minimized == "exception") {
        return "exception";
      }

      if (_expanded != null && _minchars == minChars) {
        return encoder.convert(_minimized);
      }

      try {
        _minimized = minimizer.minimizePolicies(_config, minChars);
        _minchars = minChars;
        return encoder.convert(_minimized);
      } catch (_) {
        _minimized = "exception";
        return config;
      }
    }

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
        return "exception";
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

        if (data.containsKey('date_last_ephemeral_change')) {
            if (data['date_last_ephemeral_change'] != null) {
                date_last_ephemeral_change = localDateFromAPIDate(data['date_last_ephemeral_change']);
            }
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

        if (data.containsKey('date_last_ephemeral_change')) {
            if (data['date_last_ephemeral_change'] != null) {
                date_last_ephemeral_change = localDateFromAPIDate(data['date_last_ephemeral_change']);
            }
        }

        if (data.containsKey('config')) {
            config = data['config'];
        }

        cloudtrail_entries = new List<CloudTrail>();
        if (data.containsKey('cloudtrail')) {
            for (var entry in data['cloudtrail']) {
                cloudtrail_entries.add(new CloudTrail.fromMap(entry));
            }
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
