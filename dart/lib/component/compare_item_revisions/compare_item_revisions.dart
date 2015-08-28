part of security_monkey;

@Component(
    selector: 'compare-item-revisions',
    templateUrl: 'packages/security_monkey/component/compare_item_revisions/compare_item_revisions.html',
    // cssUrl: const ['/css/bootstrap.min.css']
    useShadowDom: false
)
class CompareItemRevisions {
  ObjectStore store;
  Item base_item;
  Revision base_revision;
  List<ItemRevisionTuple> compare_item_revisions;
  bool constructor_complete = false;

  int columnWidth() {
    int number_items = compare_item_revisions.length + 1;
    return max(3, (12/number_items).round());
  }

  buildFromItems() {
    List<String> item_ids = Uri.base.fragment.split('/compare?items=')[1].split(',');
    String base_item_id = item_ids[0];
    item_ids.remove(base_item_id);
    compare_item_revisions = new List<ItemRevisionTuple>();

    this.store.one(Item, base_item_id).then((item) {
      this.base_item = item;
      this.base_revision = item.revisions.first;

      for (String item_id in item_ids) {
        if (item_id == "") {
          break;
        }
        this.store.one(Item, item_id).then((item) {
          var revision_id = item.revisions.first.id;
          store.customQueryOne(Revision,
            new CustomRequestParams(
                method: "GET",
                url:"$API_HOST/revisions/$revision_id?compare=${base_revision.id}",
                withCredentials: true
            ))
          .then( (revision) {
            this.compare_item_revisions.add(new ItemRevisionTuple(item, revision));
          });
        });
      }
    });
  }

  buildFromRevisions() {
    List<String> cri = Uri.base.fragment.split('/compare?revisions=')[1].split(',');
    String base_revision_id = cri[0];
    cri.remove(base_revision_id);

    this.store.one(Revision, base_revision_id).then((revision) {
      this.base_revision = revision;
      this.store.one(Item, revision.item_id).then((item) {
        this.base_item = item;
      });
    });

    compare_item_revisions = new List<ItemRevisionTuple>();
    for (String compare_revision_id in cri) {
      if (compare_revision_id == "") {
        break;
      }
      store.customQueryOne(Revision,
        new CustomRequestParams(
            method: "GET",
            url:"$API_HOST/revisions/$compare_revision_id?compare=$base_revision_id",
            withCredentials: true
        ))
        .then((revision) {
          this.store.one(Item, revision.item_id).then((item) {
            this.compare_item_revisions.add(new ItemRevisionTuple(item, revision));
          });
        });
    }
  }

  CompareItemRevisions(this.store){

    String fragment = Uri.base.fragment;
    if (fragment.contains('items')) {
      buildFromItems();
    } else {
      buildFromRevisions();
    }
  }

}

class ItemRevisionTuple {
  Item item;
  Revision revision;

  ItemRevisionTuple(this.item, this.revision);
}