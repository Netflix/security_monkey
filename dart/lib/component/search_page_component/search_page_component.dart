part of security_monkey;

/// Because a Search-Page contains a Search-Bar,
/// and a Search-Bar uses JavaScript and is not shadow-dom Compatible,
/// the Search-Page cannot use shadow-dom.
@Component(
    selector: 'search-page',
    templateUrl: 'packages/security_monkey/component/search_page_component/search_page_component.html',
    useShadowDom: false)
class SearchPageComponent {
    RouteProvider routeProvider;
    String current_result_type;

    SearchPageComponent(this.routeProvider) {
        this.current_result_type = this.routeProvider.route.parent.name;
    }
}
