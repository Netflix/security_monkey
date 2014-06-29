part of angular.directive;

/**
 * The `NgStyle` directive allows you to set CSS style on an HTML element conditionally.
 *
 * # example
 *
 *     <span ng-style="{color:'red'}">Sample Text</span>
 */
@Decorator(
    selector: '[ng-style]',
    map: const {'ng-style': '@styleExpression'},
    exportExpressionAttrs: const ['ng-style'])
class NgStyle {
  final dom.Element _element;
  final Scope _scope;

  String _styleExpression;
  Watch _watch;

  NgStyle(this._element, this._scope);

 /**
  * ng-style attribute takes an expression which evaluates to an
  * object whose keys are CSS style names and values are corresponding values
  * for those CSS keys.
  */
  set styleExpression(String value) {
    _styleExpression = value;
    if (_watch != null) _watch.remove();
    _watch = _scope.watch(_styleExpression, _onStyleChange, collection: true,
        canChangeModel: false);
  }

  _onStyleChange(MapChangeRecord mapChangeRecord, _) {
    if (mapChangeRecord != null) {
      dom.CssStyleDeclaration css = _element.style;
      fn(MapKeyValue m) =>
          css.setProperty(m.key, m.currentValue == null ? '' : m.currentValue);

      mapChangeRecord..forEachRemoval(fn)
                     ..forEachChange(fn)
                     ..forEachAddition(fn);
    }
  }
}
