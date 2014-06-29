part of angular.directive;

/**
 * Replaces the text content of the specified HTML element with the value of a given expression,
 * and updates the text content when the value of that expression changes. `Selector: [ng-bind]`
 *
 * Typically, you don't use ngBind directly, but instead you use the double
 * curly markup `{{ expression }}` which is similar but less verbose.
 *
 * When a page loads in the browser, the template is briefly displayed in its raw state before Angular compiles it.
 * For a large single-page app, this can result in `{{ }}` appearing while the page loads. You can prevent the template
 * bindings from showing by using `ng-bind` instead of `{{ }}`. Since `ng-bind` is an element attribute, nothing is
 * shown to the user.
 *
 * An alternative solution to this problem would be using the [NgCloak] directive.
 */
@Decorator(
  selector: '[ng-bind]',
  map: const {'ng-bind': '=>value'})
class NgBind {
  final dom.Element element;

  NgBind(this.element);

  set value(value) => element.text = value == null ? '' : value.toString();
}
