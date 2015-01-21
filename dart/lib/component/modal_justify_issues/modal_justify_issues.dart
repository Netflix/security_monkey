part of security_monkey;

@Component(
        selector: 'modaljustifyissues',
        exportExpressions: const ["is_justifying", "selectedIssues", "classForOKButton", "ok"],
        //templateUrl: 'packages/security_monkey/component/modal_justify_issues/modal_justify_issues.html',
        cssUrl: const ['/css/bootstrap.min.css']
        //useShadowDom: true
)
class ModalJustifyIssues implements ScopeAware {
    JustificationService js;
    Modal modal;
    ModalInstance modalInstance;
    Scope _scope;
    List<Issue> selectedIssues;
    String justification = "";

    bool is_justifying = false;

    ModalJustifyIssues(this.modal, this.js) { }

    void set scope(Scope scope) {
        this._scope = scope;
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
        return modal.open(new ModalOptions(templateUrl: 'packages/security_monkey/component/modal_justify_issues/modal_justify_issues.html'), _scope);
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
                _scope.rootScope.broadcast("close-issue-justification-modal", null);
                modalInstance.close(null);
                is_justifying = false;
                justification = "";
            });
        }

    }
}
