library security_monkey.item_link;

class ItemLink {
    int id;
    String name;

    ItemLink.fromMap(Map data) {
        id = data['id'];
        name = data['name'];
    }
}
