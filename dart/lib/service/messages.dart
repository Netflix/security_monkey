part of security_monkey;

@Injectable()
class Messages {
    RootScope rootScope;

    Messages(this.rootScope);

    void alert(String message) {
        rootScope.rootScope.broadcast("globalAlert", message);
    }

    void username_change(String username) {
        rootScope.rootScope.broadcast("username-change", username);
    }

    void auth_url_change(String url) {
        rootScope.rootScope.broadcast("authurl-change", url);
    }
}
