part of security_monkey;

@Component(
    selector: 'itemrevision',
    templateUrl: 'packages/SecurityMonkey/component/revision/revision_component.html',
    //cssUrl: const ['css/bootstrap.min.css'],
    publishAs: 'cmp',
    useShadowDom: false)
class RevisionComponent {
    RevisionCommentService rcs;
    UsernameService us;
    ObjectStore store;
    Revision revision;
    Revision compare_revision;
    bool show_diff = false;

    RevisionComponent(this.store, this.rcs, this.us);

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

    void set_diff(bool new_diff) {
        print("Setting diff to $new_diff");
        if (new_diff) {
            store.customQueryOne(Revision,
                    new CustomRequestParams(
                            method: "GET",
                            url:"$API_HOST/revisions/$revision_id?compare=$compare_revision_id",
                            withCredentials: true
                            ))
                   .then( (revision) {
                this.revision = revision;
                this.show_diff = true;
            });
        } else {
            show_diff = false;
        }
    }

    get rev => revision;
    get user => this.us.name;

    String addingComment;

    void addComment() {
        this.rcs.addComment(int.parse(revision_id), null, true, addingComment).then((_) {
            store.customQueryOne(Revision,
                    new CustomRequestParams(
                            method: "GET",
                            url:"$API_HOST/revisions/$revision_id?compare=$compare_revision_id",
                            withCredentials: true))
                   .then( (revision) {
                this.revision = revision;
            });
        });
    }

    void removeComment(int comment_id) {
        this.rcs.addComment(null, comment_id, false, null).then((_) {
            store.customQueryOne(Revision,
                    new CustomRequestParams(
                            method: "GET",
                            url:"$API_HOST/revisions/$revision_id?compare=$compare_revision_id",
                            withCredentials: true))
                   .then( (revision) {
                this.revision = revision;
            });
        });
    }

}
