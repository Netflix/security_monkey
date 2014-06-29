library security_monkey_model_item;

import 'package:SecurityMonkey/model/Issue.dart';
import 'package:SecurityMonkey/model/Revision.dart';
import 'package:SecurityMonkey/model/ItemComment.dart';

class Item {
  int id;
  String technology;
  String region;
  String account;
  String name;

  int num_issues = null;
  int issue_score = null;
  DateTime _first_seen = null;
  DateTime _last_seen = null;
  bool _active = null;

  List<Issue> issues = new List<Issue>();
  List<Issue> justified_issues = new List<Issue>();
  List<Issue> unjustified_issues = new List<Issue>();
  List<Revision> _revisions = new List<Revision>();
  List<ItemComment> comments = new List<ItemComment>();

  Item(data) {
    Map item = data['item'];
    id = item['id'];
    technology = item['technology'];
    region = item['region'];
    account = item['account'];
    name = item['name'];

    // These are returned in item-list so that all issues and revisions needn't be downloaded.
    if (item.containsKey('num_issues')) {
      num_issues = item['num_issues'];
    }
    if (item.containsKey('issue_score')) {
      issue_score = item['issue_score'];
    }
    if (item.containsKey('first_seen')) {
      _first_seen =  DateTime.parse(item['first_seen']);
    }
    if (item.containsKey('last_seen')) {
      _last_seen =  DateTime.parse(item['last_seen']);
    }
    if (item.containsKey('active')) {
      _active =  item['active'];
    }

    // Singular Get may also returns issues, revisions, and comments.
    if (data.containsKey('issues')) {
      for (var issue in data['issues']) {
        Issue issueObj = new Issue(issue);
        issues.add(issueObj);
        if (issueObj.justified) {
          justified_issues.add(issueObj);
        } else {
          unjustified_issues.add(issueObj);
        }
      }
    }

    if (data.containsKey('revisions')) {
      for (var revision in data['revisions']) {
        _revisions.add(new Revision(revision));
      }
    }

    if (data.containsKey('comments')) {
      for (var comment in data['comments']) {
        comments.add(new ItemComment(comment));
      }
    }
  }

  int totalScore() {
    if (issue_score != null) {
      return issue_score;
    }

    int score = 0;
    for (Issue issue in issues) {
      score = score + issue.score;
    }
    return score;
  }

  get number_issues {
    if (num_issues != null) {
      return num_issues;
    }
    return issues.length;
  }

  get has_issues => issues.length > 0;
  get has_unjustified_issues => unjustified_issues.length > 0;
  get has_justified_issues => justified_issues.length > 0;

  get revisions {
    _revisions.sort( (r1, r2) {
      return r1.date_created.isBefore(r2.date_created) ? 1 : -1;
    });
    return _revisions;
  }

  get first_seen {
    if (_first_seen != null) {
      return _first_seen;
    }

    List<Revision> revs = this.revisions;
    if (revs.length > 0)
      return revs.last.date_created;
    return null;
  }

  get last_modified {
    if (_last_seen != null) {
      return _last_seen;
    }

    List<Revision> revs = this.revisions;
    if (revs.length > 0)
      return revs.first.date_created;
    return null;
  }

  get active {
    if (_active != null) {
      return _active;
    }

    List<Revision> revs = this.revisions;
    if (revs.length > 0)
      return revs.first.active;
    return null;
  }
}