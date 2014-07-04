library security_monkey.search_page_component;

import 'package:angular/angular.dart';

@Component(
  selector: 'search-page',
  templateUrl: 'packages/SecurityMonkey/component/search_page_component/search_page_component.html',
  publishAs: 'cmp',
  useShadowDom: false) // Because a Search-Page contains a Search-Bar,
  // and a Search-Bar uses JavaScript and is not shadow-dom Compatible,
  // the Search-Page cannot use shadow-dom.
class SearchPageComponent {
  RouteProvider routeProvider;
  String current_result_type;

  SearchPageComponent(this.routeProvider) {
    this.current_result_type = this.routeProvider.route.parent.name;
  }
}