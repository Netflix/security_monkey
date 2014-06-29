part of angular.directive;

/**
 * Replaces the text content of an element with an interpolated template. `Selector: [ng-bind-template]`
 *
 * # Example
 *
 *     <div ng-bind-template="{{salutation}} {{name}}!">
 *
 * Unlike [ngBind], the `ng-bind-template` attribute can contain multiple `{{ }}` expressions.
 */
@Decorator(
    selector: '[ng-bind-template]',
    map: const {'ng-bind-template': '@bind'})
class NgBindTemplate {
  final dom.Element element;

  NgBindTemplate(this.element);

  void set bind(value) {
    element.text = value;
  }
}
