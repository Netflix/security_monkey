part of security_monkey;

@Component(
        selector: 'itemdetails',
        templateUrl: 'packages/security_monkey/component/itemdetails/itemdetails.html',
        cssUrl: const ['css/bootstrap.min.css'],
        publishAs: 'cmp'
        //useShadowDom: true
)
class ItemDetailsComponent extends ShadowRootAware {
    JustificationService js;
    UsernameService us;

    RouteProvider routeProvider;
    ShadowRoot shadowRoot;

    Item item;
    String rev_id = null;
    List<Revision> displayed_revisions;

    ObjectStore store;
    Scope scope;

    bool is_loading = true;
    bool is_error = false;
    String err_message;

    ItemDetailsComponent(this.routeProvider, this.js, this.us, this.store, this.scope) {
        scope.on("globalAlert").listen(this._showMessage);

        var item_id = this.routeProvider.parameters['itemid'];
        this.rev_id = this.routeProvider.parameters['revid'];
        displayed_revisions = new List<Revision>();

        _load_item(item_id);
    }

    Future _load_item(item_id) {
        is_loading = true;
        return store.one(Item, item_id).then((returned_item) {
            is_loading = false;
            is_error = false;

            item = returned_item;
            List revisions = item.revisions;
            int initial_revisions = min(5, revisions.length);
            _rev_index = initial_revisions;
            displayed_revisions.clear();
            displayed_revisions.addAll(revisions.sublist(0, initial_revisions));
            if (this.rev_id != null) {
                wasteASecond().then((_) {
                    scrollTo(int.parse(rev_id));
                });
            }
        });
    }

    void _showMessage(ScopeEvent event) {
        is_loading = false;
        this.is_error = true;
        this.err_message = event.data;
    }

    int _rev_index = 0;
    void loadMore() {
        List revisions = item.revisions;
        //print("Inside loadMore. $_rev_index of ${revisions.length}");
        if (_rev_index < revisions.length) {
            displayed_revisions.add(revisions.elementAt(_rev_index++));
        }
    }

    get user => us.name;

    String auditClassForItem() {
        for (Issue issue in item.issues) {
            if (!issue.justified) {
                return "list-group-item-danger";
            }
        }
        return "list-group-item-success";
    }

    String classForIssue(bool isJustified) {
        return isJustified ? "panel-success" : "panel-danger";
    }

    String addingComment;

    void addComment() {
        var ic = new ItemComment()
                ..text=addingComment;

        store.scope(item).create(ic).then((_) {
            _load_item(item.id).then( (_) {
                addingComment = "";
            });
        });
    }

    void removeComment(int comment_id) {
        var ic = new ItemComment()
            ..id = comment_id;

        store.scope(item).delete(ic).then((_) {
            _load_item(item.id);
        });

    }

    /// Let angular have a second to ng-repeat through all the revisions options
    /// (Angular needs to insert these revisions into the DOM before we can
    /// find them with the querySelector and call scrollIntoView() ).
    Future wasteASecond() {
        return new Future.delayed(const Duration(milliseconds: 500), () => "1");
    }

    bool _revid_is_displayed(int revid) {
        for (Revision r in this.displayed_revisions) {
            if (r.id == revid) {
                return true;
            }
        }
        return false;
    }

    bool _is_valid_revid(int revid) {
        for (Revision r in this.item.revisions) {
            if (r.id == revid) {
                return true;
            }
        }
        return false;
    }

    Future _loadUntilRevision(int revid) {
        if (!this._is_valid_revid(revid)) {
            print("Asked to scroll to an invalid revision: $revid");
            return new Future.error("Asked to scroll to an invalid revision: $revid");
        }

        while (!this._revid_is_displayed(revid)) {
            this.loadMore();
        }
        return new Future.value("Success");
    }

    void _scrollTo(int revid) {
        print("Asked to scroll to revision $revid");
        var item = shadowRoot.querySelector("#rev_id_$revid");
        item.scrollIntoView(ScrollAlignment.TOP);
                //ScrollAlignment.CENTER);
    }

    void scrollTo(int revid) {
        if (_revid_is_displayed(revid)) {
            this._scrollTo(revid);
        } else {
            this._loadUntilRevision(revid).then((_) {
                this.wasteASecond().then((_) {
                    this._scrollTo(revid);
                });
            });
        }
    }

    void onShadowRoot(ShadowRoot shadowRoot) {
        this.shadowRoot = shadowRoot;
    }

    String justification = "";
    void justify() {
        List<Future> justification_futures = new List<Future>();

        for (Issue issue in item.issues) {
            if (issue.selected_for_justification) {
                justification_futures.add(js.justify(issue.id, justification));
            }

            Future.wait(justification_futures).then((_) {
                print("Done justifying all issues.");
                _load_item(item.id).then( (_) {
                    justification = "";
                });
            });
        }
    }

    void removeJustification(var issue_id) {
        js.unjustify(issue_id).then((_) {
            _load_item(item.id);
        });
    }

    int prev_rev(int rev_id) {
        bool found = false;
        for (Revision rev in item.revisions) {
            if (found) {
                return rev.id;
            }

            if (rev.id == rev_id) {
                found = true;
            }
        }
        return rev_id;
    }

}
