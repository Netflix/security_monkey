library security_monkey.revision_component;

import 'package:angular/angular.dart';
import 'package:SecurityMonkey/service/revision_comment_service.dart';
import 'package:SecurityMonkey/service/revision_service.dart';
import 'package:SecurityMonkey/service/username_service.dart';
import 'package:SecurityMonkey/model/Revision.dart';

@Component(
    selector: 'itemrevision',
    templateUrl: 'packages/SecurityMonkey/component/revision/revision_component.html',
    //cssUrl: const ['css/bootstrap.min.css'],
    publishAs: 'cmp',
    useShadowDom: false
)
class RevisionComponent {
  RevisionCommentService rcs;
  RevisionService rs;
  UsernameService us;
  Revision revision;
  Revision compare_revision;


  String _ri;
  @NgAttr('revision_id')
  set revision_id(ri) {
    _ri = ri;
//    this.rs.loadData(revision_id).then((new_revision) {
//      revision = new_revision;
//    });
  }
  get revision_id => _ri;

  String _cri;
  @NgAttr('compare_revision_id')
  set compare_revision_id(cri) {
    _cri = cri;
    this.rs.loadData(revision_id, compare_revision_id).then((new_revision) {
      revision = new_revision;
    });
  }
  get compare_revision_id => _cri;

  bool hasDiffHtml() {
    if (revision != null && revision.diff_html != null)
      return true;
    return false;
  }

  String panelClassForRevision() {
    if (revision == null || !revision.active) {
      return "default";
    } else {
      return "success";
    }
  }


  RevisionComponent(this.rs, this.rcs, this.us);

  get rev => revision;
  get user => this.us.name;

  String addingComment;

  void addComment() {
    this.rcs.addComment(int.parse(revision_id), null, true, addingComment)
      .then( (_) {
        this.rs.loadData(revision_id, compare_revision_id).then((new_revision) {
            revision = new_revision;
            addingComment = "";
        });
      });
  }

  void removeComment(int comment_id) {
    this.rcs.addComment(null, comment_id, false, null)
      .then( (_) {
        this.rs.loadData(revision_id).then((new_revision) {
            revision = new_revision;
        });
      });
  }

}