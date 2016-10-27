part of security_monkey;

@Component(
    selector: 'ignorelist-cmp',
    templateUrl: 'packages/security_monkey/component/settings/ignore_list_component/ignore_list_component.html',
    //cssUrl: const ['/css/bootstrap.min.css']
    useShadowDom: false
)
class IgnoreListComponent extends PaginatedTable {
    UsernameService us;
    Router router;
    List<IgnoreEntry> ignorelist;
    ObjectStore store;

    IgnoreListComponent(this.router, this.store, this.us) {
        ignorelist = new List<IgnoreEntry>();
        list();
    }

    get signed_in => us.signed_in;

    void list() {
        store.list(IgnoreEntry, params: {
            "count": ipp_as_int,
            "page": currentPage
        }).then((ignorelist) {
            super.setPaginationData(ignorelist.meta);
            this.ignorelist = ignorelist;
            super.is_loaded = true;
        });
    }

    void createIgnoreEntry() {
        router.go('createignoreentry', {});
    }

    void deleteIgnoreList(ignoreitem) {
        store.delete(ignoreitem).then( (_) {
            store.list(IgnoreEntry).then( (ignoreitems) {
                this.ignorelist = ignoreitems;
            });
        });
    }

    String url_encode(input) => param_to_url(input);

    get isLoaded => super.is_loaded;
    get isError => super.is_error;
}
