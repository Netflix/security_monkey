part of angular.directive;
/**
 * Specifies a base CSS to use for components defined under the directive. `Selector: [ng-base-css]`
 *
 * The NgBaseCss directive is typically used at the top of an Angular application, so that everything in the
 * application inherits the specified stylesheet.
 *
 * # Example
 *     <div ng-base-css="my_application.css">
 */
@Decorator(selector: '[ng-base-css]')
class NgBaseCss {
  List<String> _urls = const [];

  @NgAttr('ng-base-css')
  set urls(v) => _urls = v is List ? v : [v];

  List<String> get urls => _urls;
}
