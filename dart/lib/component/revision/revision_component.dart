part of security_monkey;

@Component(
    selector: 'itemrevision',
    templateUrl: 'packages/security_monkey/component/revision/revision_component.html',
    //cssUrl: const ['/css/bootstrap.min.css'],
    useShadowDom: false)
class RevisionComponent {
    UsernameService us;
    ObjectStore store;
    Revision revision;

    RevisionComponent(this.store, this.us);

    String _ri;
    @NgAttr('revision_id')
    set revision_id(ri) {
        _ri = ri;
        this.store.one(Revision, ri).then((revision) {
            this.revision = revision;
        });
    }
    get revision_id => _ri;

    String _cri;
    @NgAttr('compare_revision_id')
    set compare_revision_id(cri) {
        _cri = cri;
    }
    get compare_revision_id => _cri;

    bool hasDiffHtml() {
        if (revision != null && revision.diff_html != null) return true;
        return false;
    }

    String panelClassForRevision() {
        if (revision == null || !revision.active) {
            return "default";
        } else {
            return "success";
        }
    }

    bool has_expanded_section() {
      if (revision != null) {
        return revision.has_expanded();
      } else {
        return false;
      }
    }

    var display_tab = 'current';
    void select_tab(var new_tab) {
      display_tab = new_tab;
      if (new_tab == 'diff') {
        store.customQueryOne(Revision,
                new CustomRequestParams(
                        method: "GET",
                        url:"$API_HOST/revisions/$revision_id?compare=$compare_revision_id",
                        withCredentials: true
                        ))
               .then( (revision) {
            this.revision = revision;
        });
      }
    }

    get rev => revision;
    get user => this.us.name;

    String addingComment;

    void addComment() {

        var rc = new RevisionComment()
                ..text = addingComment;

        store.scope(revision).create(rc).then((_) {
            store.customQueryOne(Revision,
                    new CustomRequestParams(
                            method: "GET",
                            url:"$API_HOST/revisions/$revision_id?compare=$compare_revision_id",
                            withCredentials: true))
                   .then( (revision) {
                this.revision = revision;
                addingComment = "";
            });
        });
    }

    void removeComment(int comment_id) {

        var rc = new RevisionComment()
            ..id = comment_id;

        store.scope(revision).delete(rc).then((_) {
            store.customQueryOne(Revision,
                    new CustomRequestParams(
                            method: "GET",
                            url:"$API_HOST/revisions/$revision_id?compare=$compare_revision_id",
                            withCredentials: true))
                   .then( (revision) {
                this.revision = revision;
                addingComment = "";
            });
        });
    }

}
