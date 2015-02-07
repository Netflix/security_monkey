part of security_monkey;

@Component(
    selector: 'settings-cmp',
    templateUrl: 'packages/security_monkey/component/settings_component/settings_component.html',
    //cssUrl: const ['/css/bootstrap.min.css']
    useShadowDom: false
)
class SettingsComponent extends PaginatedTable {
    Router router;
    List<Account> accounts;
    List<NetworkWhitelistEntry> cidrs;
    List<IgnoreEntry> ignorelist;
    ObjectStore store;
    UserSetting user_setting;

    SettingsComponent(this.router, this.store) {
        cidrs = new List<NetworkWhitelistEntry>();
        accounts = new List<Account>();
        store.customQueryOne(UserSetting, new CustomRequestParams(method: "GET", url: "$API_HOST/settings", withCredentials: true)).then((user_setting) {
            this.user_setting = user_setting;
            list();
        });

        store.list(NetworkWhitelistEntry).then( (cidrs) {
           this.cidrs = cidrs;
        });

        store.list(IgnoreEntry).then( (ignoreItems) {
           this.ignorelist = ignoreItems;
        });
    }

    void list() {
        store.list(Account, params: {
            "count": ipp_as_int,
            "page": currentPage
        }).then((accounts) {
            super.setPaginationData(accounts.meta);
            this.accounts = accounts;
            super.is_loaded = true;
        });
    }

    bool enabledValueForAccount(bool active, bool third_party) {
        return active && (third_party == false);
    }

    bool notificationValueForAccount(var id) {
        if (user_setting == null) {
            return false;
        }

        for (Account account in user_setting.accounts) {
            if (account.id == id) {
                return true;
            }
        }
        return false;
    }

    void toggleNotificationForAccount(var id) {
        // Remove existing accounts.
        for (Account account in user_setting.accounts) {
            if (account.id == id) {
                user_setting.accounts.remove(account);
                return;
            }
        }

        // Add new accounts
        for (Account account in this.accounts) {
            if (account.id == id) {
                user_setting.accounts.add(account);
                return;
            }
        }
    }

    void saveNotificationSettings() {
        super.is_loaded = false;
        store.customCommand(user_setting,
                new CustomRequestParams(
                        method: 'POST',
                        url: '$API_HOST/settings',
                        data: user_setting.toJson(),
                        withCredentials: true)).then((_) {
            // Poor way to give feedback of success:
            super.is_loaded = true;
        });
    }

    void createAccount() {
        router.go('createaccount', {});
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


    get isLoaded => super.is_loaded;
    get isError => super.is_error;
}
