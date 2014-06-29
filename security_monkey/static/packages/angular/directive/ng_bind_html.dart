part of angular.directive;

/**
 * Sanitizes an HTML string and invokes the browser's parser to insert the string into
 * the containing element in the DOM. `Selector: [ng-bind-html]`
 *
 * # Example
 *
 *     <div ng-bind-html="expression"></div>
 *
 * The expression must evaluate to a string. Content is sanitized using a default [NodeValidator].
 */
@Decorator(
  selector: '[ng-bind-html]',
  map: const {'ng-bind-html': '=>value'})
class NgBindHtml {
  final dom.Element element;
  final dom.NodeValidator validator;

  NgBindHtml(this.element, dom.NodeValidator this.validator);

  /**
   * Parsed expression from the `ng-bind-html` attribute. 
   *
   * The result of this expression is inserted into the containing element in the DOM according to the
   * rules specified in the documentation for the class.
   */
  void set value(value) => element.setInnerHtml(
      value == null ? '' : value.toString(), validator: validator);
}
