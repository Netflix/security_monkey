part of security_monkey;

@Component(
  selector: 'user-role-cmp',
  templateUrl: 'packages/security_monkey/component/settings/user_role_component/user_role_component.html',
  useShadowDom: false
)
class UserRoleComponent extends PaginatedTable {
    UsernameService us;
    ObjectStore store;
    List<User> users;
    List<Role> roles;

    UserRoleComponent(this.store, this.us) {
        users = new List<User>();
        roles = new List<Role>();
        list();
    }

    get isLoaded => super.is_loaded;
    get isError => super.is_error;

    void list() {
        super.is_loaded = false;
        bool users_loaded = false;
        bool roles_loaded = false;

        store.list(User, params: {
            "count": ipp_as_int,
            "page": currentPage,
            "order_by": sorting_column,
            "order_dir": order_dir()
        }).then((users_response) {
            super.setPaginationData(users_response.meta);
            this.users = users_response;
            users_loaded = true;
            if (roles_loaded) {
                super.is_loaded = true;
            }
        });
            
        store.list(Role).then((roles_response) {
            this.roles = roles_response;
            roles_loaded = true;
            if (users_loaded) {
                super.is_loaded = true;
            }
        });

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
            list();
        }
        void handleError(String e){
            // alert("Error: User cannot be deleted");
        }

        f.then((value) => handleValue(value))
        .catchError((error) => handleError(error));
    }
}