part of security_monkey;

@Component(
        selector: 'signout',
        templateUrl: 'packages/security_monkey/component/signout_component/signout_component.html',
        exportExpressions: const ["complete"],
        //cssUrl: const ['/css/bootstrap.min.css'],
        useShadowDom: false
)
class SignoutComponent implements ScopeAware {
    final Http _http;
    bool _complete = false;
    bool error = false;
    bool loading = true;
    Scope scope;

    set complete(val) {
        if (val) {
            scope.rootScope.broadcast("username-change", "");
        }
        _complete = val;
    }

    get complete => _complete;

    SignoutComponent(this._http) {
        String url = '$API_HOST/logout';
        print("Signing Out...");
        _http.get(url, withCredentials: true).then((HttpResponse response) {
            print("Sign Out Complete");
            complete = true;
            loading = false;

        }).catchError((error) {
            print("Error Signing Out $error");
            error = true;
            loading = false;
        });
    }

}
