part of security_monkey;

@Component(
    selector: 'whitelist-cmp',
    templateUrl: 'packages/security_monkey/component/settings/network_whitelist_component/network_whitelist_component.html',
    //cssUrl: const ['/css/bootstrap.min.css']
    useShadowDom: false
)
class NetworkWhitelistComponent extends PaginatedTable {
    UsernameService us;
    Router router;
    List<NetworkWhitelistEntry> cidrs;
    ObjectStore store;

    NetworkWhitelistComponent(this.router, this.store, this.us) {
        cidrs = new List<NetworkWhitelistEntry>();
        list();
    }

    get signed_in => us.signed_in;

    void list() {
        store.list(NetworkWhitelistEntry, params: {
            "count": ipp_as_int,
            "page": currentPage
        }).then((cidrs) {
            super.setPaginationData(cidrs.meta);
            this.cidrs = cidrs;
            super.is_loaded = true;
        });
    }

    void createWhitelist() {
        router.go('createwhitelist', {});
    }

    void deleteWhitelist(NetworkWhitelistEntry cidr){
        store.delete(cidr).then( (_) {
            store.list(NetworkWhitelistEntry).then( (cidrs) {
               this.cidrs = cidrs;
            });
        });
    }

    String url_encode(input) => param_to_url(input);

    get isLoaded => super.is_loaded;
    get isError => super.is_error;
}
