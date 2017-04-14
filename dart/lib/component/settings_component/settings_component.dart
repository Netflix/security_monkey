part of security_monkey;

@Component(
    selector: 'settings-cmp',
    templateUrl: 'packages/security_monkey/component/settings_component/settings_component.html',
    //cssUrl: const ['/css/bootstrap.min.css']
    useShadowDom: false
)
class SettingsComponent extends PaginatedTable {
    UsernameService us;
    Router router;
    List<Account> accounts;
    List<AuditorSetting> auditorlist;
    ObjectStore store;
    UserSetting user_setting;
    bool active_edit_mode = false;


    SettingsComponent(this.router, this.store, this.us) {
        accounts = new List<Account>();
        store.customQueryOne(UserSetting, new CustomRequestParams(method: "GET", url: "$API_HOST/settings", withCredentials: true)).then((user_setting) {
            this.user_setting = user_setting;
            list();
        });

        store.list(AuditorSetting).then( (auditorItems) {
            this.auditorlist = auditorItems;
        });
    }

    get signed_in => us.signed_in;

    void list() {
        store.list(Account, params: {
            "count": ipp_as_int,
            "page": currentPage,
            "order_by": sorting_column,
            "order_dir": order_dir()
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
                        withCredentials: true,
                        xsrfCookieName: 'XSRF-COOKIE',
                        xsrfHeaderName:'X-CSRFToken')).then((_) {
            // Poor way to give feedback of success:
            super.is_loaded = true;
        });
    }

    void createAccount() {
        router.go('createaccount', {});
    }

    void toggleActiveEditMode() {
        super.is_loaded = false;
        this.active_edit_mode = true;
        super.is_loaded = true;
    }

    void storeActive() {
        super.is_loaded = false;
        AccountBulkUpdate bulkUpdate = new AccountBulkUpdate.fromAccountList(this.accounts);

        this.store.update(bulkUpdate).then((_) {
            this.active_edit_mode = false;
            super.is_loaded = true;
        });
    }

    void disableAuditor(auditor) {
        auditor.disabled = true;
        store.update(auditor);
    }

    void enableAuditor(auditor) {
        auditor.disabled = false;
        store.update(auditor);
    }

    String url_encode(input) => param_to_url(input);

    get isLoaded => super.is_loaded;
    get isError => super.is_error;
}
