library security_monkey.itemdetails;

import 'package:angular/angular.dart';
import 'package:SecurityMonkey/service/itemdetails_service.dart';
import 'package:SecurityMonkey/service/justify_service.dart';
import 'package:SecurityMonkey/service/item_comment_service.dart';
import 'package:SecurityMonkey/service/username_service.dart';

import 'dart:html';
import 'dart:async';
import 'dart:math';

import 'package:SecurityMonkey/model/Item.dart';
import 'package:SecurityMonkey/model/Issue.dart';
import 'package:SecurityMonkey/model/Revision.dart';

@Component(selector: 'itemdetails', templateUrl: 'packages/SecurityMonkey/component/itemdetails/itemdetails.html', cssUrl: const ['css/bootstrap.min.css'], publishAs: 'cmp'//useShadowDom: true
)
class ItemDetailsComponent extends ShadowRootAware {
    ItemDetailsService ids;
    JustifyService js;
    ItemCommentService ics;
    UsernameService us;
    RouteProvider routeProvider;
    Item item;
    ShadowRoot shadowRoot;
    String rev_id = null;
    List<Revision> displayed_revisions;

    get isLoading => ids.isLoaded;
    get isError => ids.isError;
    get errMessage => ids.errMessage;

    ItemDetailsComponent(this.ids, this.routeProvider, this.js, this.ics, this.us) {
        var item_id = this.routeProvider.parameters['itemid'];
        this.rev_id = this.routeProvider.parameters['revid'];
        displayed_revisions = new List<Revision>();
        ids.loadData(item_id).then((returned_item) {
            item = returned_item;
            List revisions = item.revisions;
            int initial_revisions = min(5, revisions.length);
            _rev_index = initial_revisions;
            print("Adding from 0 to $initial_revisions");
            displayed_revisions.addAll(revisions.sublist(0, initial_revisions));
            if (this.rev_id != null) {
                wasteASecond().then((_) {
                    scrollTo(int.parse(rev_id));
                });
            }
        });
    }

    int _rev_index = 0;
    void loadMore() {
        List revisions = item.revisions;
        print("Inside loadMore. $_rev_index of ${revisions.length}");
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
        this.ics.addComment(item.id, null, true, addingComment).then((_) {
            ids.loadData(item.id).then((returned_item) {
                item = returned_item;
                addingComment = "";
            });
        });
    }

    void removeComment(int comment_id) {
        this.ics.addComment(null, comment_id, false, null).then((_) {
            ids.loadData(item.id).then((returned_item) {
                item = returned_item;
            });
        });
    }

    // Let angular have a second to ng-repeat through all the revisions options
    // (Angular needs to insert these revisions into the DOM before we can
    // find them with the querySelector and call scrollIntoView() ).
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
        print("Inside onShadowRoot");
        this.shadowRoot = shadowRoot;
    }

    String justification = "";
    void justify() {
        List<Future> justification_futures = new List<Future>();

        for (Issue issue in item.issues) {
            if (issue.selected_for_justification) {
                justification_futures.add(js.justify(issue.id, true, justification));
            }

            Future.wait(justification_futures).then((_) {
                print("Done justifying all issues.");
                ids.loadData(this.item.id).then((returned_item) {
                    item = returned_item;
                    justification = "";
                    print("Done reloading after justificaitons");
                });
            });
        }
    }

    void removeJustification(var issue_id) {
        js.justify(issue_id, false, "-").then((_) {
            ids.loadData(this.item.id).then((returned_item) {
                item = returned_item;
            });
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
