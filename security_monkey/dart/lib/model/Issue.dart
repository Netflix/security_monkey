library security_monkey.model_issue;

import 'Item.dart';
import 'ItemLink.dart';
import 'package:security_monkey/util/utils.dart' show localDateFromAPIDate;

class Issue {
    int id;
    int score;
    String issue;
    String notes;
    bool fixed;
    bool justified;
    String justified_user;
    String justification;
    //String justified_date;
    DateTime justified_date;
    int item_id;
    bool selected_for_justification;

    Item item;
    List<ItemLink> item_links = new List<ItemLink>();

    Issue.fromMap(Map data) {
        id = data['id'];
        score = data['score'];
        issue = data['issue'];
        notes = data['notes'];
        fixed = data['fixed'];
        justified = data['justified'];
        justified_user = data['justified_user'];
        justification = data['justification'];
        if (data['justified_date'] != null) {
            justified_date = localDateFromAPIDate(data['justified_date']);
        }
        item_id = data['item_id'];
        selected_for_justification = false;

        item = new Item.fromMap({
            "item": data
        });

        for (var item_link in data['item_links']) {
          ItemLink linkObj = new ItemLink.fromMap(item_link);
          item_links.add(linkObj);
        }
    }

    get has_sub_item => this.item_links.length != 0;

    get get_links => '<a href="#/viewitem/{{item_links.first.id}}">{{item_links.first.name}}</a>';
}
