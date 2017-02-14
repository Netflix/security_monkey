part of security_monkey;

@Component(
    selector: 'audit-score-cmp',
    templateUrl: 'packages/security_monkey/component/settings/audit_score_component/audit_score_component.html',
    useShadowDom: false
)

class AuditScoreListComponent extends PaginatedTable {
    UsernameService us;
    Router router;
    List<AuditScore> auditscores;
    ObjectStore store;

    get isLoaded => super.is_loaded;
    get isError => super.is_error;

    AuditScoreListComponent(this.router, this.store, this.us) {
        list();
    }

    void list() {
        super.is_loaded = false;
        store.list(AuditScore, params: {
            "count": ipp_as_int,
            "page": currentPage,
        }).then((auditscores) {
            super.setPaginationData(auditscores.meta);
            this.auditscores = auditscores;
            super.is_loaded = true;
        });
    }

    void createAuditScore() {
        router.go('createauditscore', {});
    }

    void deleteAuditScoreList(auditscoreitem) {
        store.delete(auditscoreitem).then( (_) {
            store.list(AuditScore).then( (auditscoreitems) {
                this.auditscores = auditscoreitems;
            });
        });
        list();
    }
}
