part of security_monkey;

@Component(
        selector: 'modaljustifyissues',
        //templateUrl: 'packages/security_monkey/component/modal_justify_issues/modal_justify_issues.html',
        cssUrl: const ['css/bootstrap.min.css'],
        publishAs: 'cmp'
        //useShadowDom: true
)
class ModalJustifyIssues {
    JustificationService js;
    Modal modal;
    ModalInstance modalInstance;
    Scope scope;
    List<Issue> selectedIssues;
    String justification = "";

    bool is_justifying = false;

    String template = """
<div class="modal-header">
  <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
  <h4 class="modal-title">Justify {{ cmp.selectedIssues.length }} issues.</h4>
</div>
<div class="modal-body" ng-if="!cmp.is_justifying">
  <table class="table table-striped">
    <thead>
      <tr>
        <th>Item Name</th>
        <th>Technology</th>
        <th>Account</th>
        <th>Region</th>
        <th>Issue</th>
        <th>Notes</th>
        <th>Score</th>
      </tr>
    </thead>
    <tbody>
      <tr ng-repeat="issue in cmp.selectedIssues" ng-switch="issue.justified">
        <td>{{issue.item.name}}</td>
        <td>{{issue.item.technology}}</td>
        <td>{{issue.item.account}}</td>
        <td>{{issue.item.region}}</td>
        <td>{{issue.issue}}</td>
        <td>{{issue.notes}}</td>
        <td>{{issue.score}}</td>
      </tr>
    </tbody>
  </table>
  <hr />
  <div class="form-group">
    <label for="Justification" class="col-sm-2 control-label">Justification</label>
    <div class="col-sm-10">
      <input type="text" class="form-control" placeholder="This is allowed because ... (512 characters)" ng-model="cmp.justification" maxlength="512">
    </div>
  </div>
  <br />
</div>
<div class="modal-body" ng-if="cmp.is_justifying">
    <p>Justifying ...</p>
</div>
<div class="modal-footer">
  <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
  <button type="button" class="btn btn-primary {{ cmp.classForOKButton() }}" ng-click="cmp.ok()">OK</button>
</div>
""";

    ModalJustifyIssues(this.modal, this.scope, this.js) {
        scope.on('open-issue-justification-modal').listen(openModal);
    }

    void openModal(ScopeEvent e) {
        selectedIssues = [];
        for(Issue issue in e.data) {
            if (!issue.justified) {
                selectedIssues.add(issue);
            }
        }
        if (selectedIssues.length > 0) {
            open();
        } else {
            print("Cannot justify already issues that are already justified.");
        }
    }

    String classForOKButton() {
        if (justification.length > 0 && justification.length <=512) {
            return "";
        }
        return "disabled";
    }

    ModalInstance getModalInstance() {
        return modal.open(new ModalOptions(template: template), scope);
    }

    void open() {
        modalInstance = getModalInstance();

        modalInstance.opened..then((v) {
                    print('Opened');
                }, onError: (e) {
                    print('Open error is $e');
                });

        // Override close to add you own functionality
        modalInstance.close = (_) {
            modal.hide();
        };
        // Override dismiss to add you own functionality
        modalInstance.dismiss = (String reason) {
            print('Dismissed with $reason');
            modal.hide();
        };
    }

    void ok() {
        is_justifying = true;
        List<Future> justification_futures = new List<Future>();

        for (Issue issue in selectedIssues) {
            if (issue.selected_for_justification) {
                justification_futures.add(js.justify(issue.id, justification));
            }

            Future.wait(justification_futures).then((_) {
                print("Done justifying all issues.");
                scope.rootScope.broadcast("close-issue-justification-modal", null);
                modalInstance.close(null);
                is_justifying = false;
                justification = "";
            });
        }

    }
}
