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
    List<User> users;
    List<Role> roles;
    List<NetworkWhitelistEntry> cidrs;
    List<IgnoreEntry> ignorelist;
    List<AuditorSetting> auditorlist;
    ObjectStore store;
    UserSetting user_setting;
    
    SettingsComponent(this.router, this.store, this.us) {
        cidrs = new List<NetworkWhitelistEntry>();
        accounts = new List<Account>();
        users = new List<User>();
        roles = new List<Role>();
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

        store.list(AuditorSetting).then( (auditorItems) {
            this.auditorlist = auditorItems;
        });

        store.list(User).then( (Users) {
            this.users = Users;
        });
        
        store.list(Role).then( (Roles) {
            this.roles = Roles;
        });
    }
    
    get signed_in => us.signed_in;
    
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

    void disableAuditor(auditor) {
        auditor.disabled = true;
        store.update(auditor);
    }

    void enableAuditor(auditor) {
        auditor.disabled = false;
        store.update(auditor);
    }
    
    void enableUser(User user){
      user.active = true;
      store.update(user);
    }
    
    void disableUser(User user){
      user.active = false;
      store.update(user);
    }
    
    void changeRole(User user){
      var elements = document.getElementsByClassName("changeRole");
      for(Node element in elements){
        if(element.parent.parent.attributes["data-uid"] == user.id.toString()){
          SelectElement el = element;
          String role_id = el.value;
          Role role;
          for(Role r in this.roles){
            if (r.id == role_id){
              role = r;
            }
          }
          user.role = role;
          store.update(user);
        }
      }
    }
    
    //TODO (Olly) add "Are you sure" dialog
    void deleteUser(User user){
      Future f = store.delete(user);
      
      void handleValue(CommandResponse v){
        store.list(User).then( (Users) {
                    this.users = Users;
                });
      }
      void handleError(String e){
//        alert("Error: User cannot be deleted");
      }
      
      f.then((value) => handleValue(value))
      .catchError((error) => handleError(error));
    }
    
    String url_encode(input) => param_to_url(input);

    get isLoaded => super.is_loaded;
    get isError => super.is_error;
}
