part of angular.directive;

/**
 * The `ngClass` directive allows you to dynamically style an HTML element,
 * by binding to an expression that represents the classes to be bound. `Selector: [ng-class]`
 *
 * Classes are specified by a bound model that can be a string, array, or map:
 *
 *  * String syntax: If the expression is a space-delimited list of CSS classes,
 *    CSS classes within the string are additively applied to the element.
 *  * Array syntax: If the expression is an array, CSS classes are additively applied to the
 *    element.
 *  * Map syntax: If the expression is a map of 'key':value pairs, then the truthiness of the
 *    value is used to determine which CSS classes are applied. (Here, the keys correspond to the
 *    CSS classes to be applied.)
 *
 * The directive won't add duplicate classes if a particular class was already set. When the
 * expression changes, CSS classes are updated to reflect the change.
 *
 * # Examples
 *
 * Let's assume that we have a simple stylesheet that defines three CSS classes for the following
 * examples.
 *
 *     .text-remove {
 *       text-decoration: line-through;
 *     }
 *     .strong {
 *         font-weight: bold;
 *     }
 *     .alert {
 *         color: red;
 *     }
 *
 * ## String Syntax
 *
 *     <input type="text" ng-model="style"
 *         placeholder="Type an expression here, e.g.: strong
 *     text-remove alert">
 *     <p ng-class="style">Using String Syntax</p>
 *
 * When the user types a string into the text box, it's evaluated as a list of CSS classes to be
 * applied to the <p> element on which `ng-class` is applied. For example,
 * "strong text-remove" applies both `bold` and `line-through` to the text "Using String Syntax".
 *
 * ## Array Syntax
 *
 *     <input ng-model="style1"
 *        placeholder="Type an expression, e.g. strong:"><br>
 *     <input ng-model="style2"
 *        placeholder="Type an expression, e.g. text-remove:"><br>
 *     <input ng-model="style3"
 *        placeholder="Type an expression, e.g. alert:"><br>
 *     <p ng-class="[style1, style2, style3]">Using Array Syntax</p>
 *
 * Here the array is defined by the input in three text boxes. Typing a CSS class name
 * into each box additively applies those CSS classes to the text "Using Array Syntax".
 *
 * ## Map Syntax
 *
 *     <input type="checkbox" ng-model="bold"> apply "strong" class
 *     <input type="checkbox" ng-model="deleted"> apply "text-remove" class
 *     <input type="checkbox" ng-model="caution"> apply "alert" class
 *     <p ng-class="{
 *         'text-remove': deleted,
 *         'strong': bold,
 *         'alert': caution}">
 *        Map Syntax Example</p>
 *
 * Here the map associates CSS classes to the input checkboxes. If a checkbox evaluates to true,
 * that style is applied additively to the text "Map Syntax Example". Note that the class
 * names are escaped in single quotes, since the map keys represent strings.
 *
 */
@Decorator(
    selector: '[ng-class]',
    map: const {'ng-class': '@valueExpression'},
    exportExpressionAttrs: const ['ng-class'])
class NgClass extends _NgClassBase {
  NgClass(NgElement ngElement, Scope scope, NodeAttrs nodeAttrs)
      : super(ngElement, scope, nodeAttrs);
}

/**
 * Dynamically style only odd rows in a list via data.
 *
 * The `ngClassOdd` and `ngClassEven` directives work exactly as
 * {@link ng.directive:ngClass ngClass}, except it works in
 * conjunction with `ngRepeat` and takes affect only on odd (even) rows.
 *
 * This directive can be applied only within a scope of an `ngRepeat`.
 *
 * ##Examples
 *
 * index.html:
 *
 *     <li ng-repeat="name in ['John', 'Mary', 'Cate', 'Suz']">
 *       <span ng-class-odd="'odd'" ng-class-even="'even'">
 *         {{name}}
 *       </span>
 *     </li>
 *
 * style.css:
 *
 *     .odd {
 *       color: red;
 *     }
 *     .even {
 *       color: blue;
 *     }
 */
@Decorator(
    selector: '[ng-class-odd]',
    map: const {'ng-class-odd': '@valueExpression'},
    exportExpressionAttrs: const ['ng-class-odd'])
class NgClassOdd extends _NgClassBase {
  NgClassOdd(NgElement ngElement, Scope scope, NodeAttrs nodeAttrs)
      : super(ngElement, scope, nodeAttrs, 0);
}

/**
 * The `ngClassOdd` and `ngClassEven` directives work exactly as
 * {@link ng.directive:ngClass ngClass}, except it works in
 * conjunction with `ngRepeat` and takes affect only on odd (even) rows.
 *
 * This directive can be applied only within a scope of an `ngRepeat`.
 *
 * ##Examples
 *
 * index.html:
 *
 *     <li ng-repeat="name in ['John', 'Mary', 'Cate', 'Suz']">
 *       <span ng-class-odd="'odd'" ng-class-even="'even'">
 *         {{name}}
 *       </span>
 *     </li>
 *
 * style.css:
 *
 *     .odd {
 *       color: red;
 *     }
 *     .even {
 *       color: blue;
 *     }
 */
@Decorator(
    selector: '[ng-class-even]',
    map: const {'ng-class-even': '@valueExpression'},
    exportExpressionAttrs: const ['ng-class-even'])
class NgClassEven extends _NgClassBase {
  NgClassEven(NgElement ngElement, Scope scope, NodeAttrs nodeAttrs)
      : super(ngElement, scope, nodeAttrs, 1);
}

abstract class _NgClassBase {
  final NgElement _ngElement;
  final Scope _scope;
  final int _mode;
  Watch _watchExpression;
  Watch _watchPosition;
  var _previousSet = new Set<String>();
  var _currentSet = new Set<String>();
  bool _first = true;

  _NgClassBase(this._ngElement, this._scope, NodeAttrs nodeAttrs,
               [this._mode = null])
  {
    var prevCls;

    nodeAttrs.observe('class', (String cls) {
      if (prevCls != cls) {
        prevCls = cls;
        _applyChanges(_scope.context[r'$index']);
      }
    });
  }

  set valueExpression(expression) {
    if (_watchExpression != null) _watchExpression.remove();
    _watchExpression = _scope.watch(expression, (v, _) {
        _computeChanges(v);
        _applyChanges(_scope.context[r'$index']);
      },
      canChangeModel: false,
      collection: true);

    if (_mode != null) {
      if (_watchPosition != null) _watchPosition.remove();
      _watchPosition = _scope.watch(r'$index', (idx, previousIdx) {
        var mod = idx % 2;
        if (previousIdx == null || mod != previousIdx % 2) {
          if (mod == _mode) {
            _currentSet.forEach((cls) => _ngElement.addClass(cls));
          } else {
            _previousSet.forEach((cls) => _ngElement.removeClass(cls));
          }
        }
      }, canChangeModel: false);
    }
  }

  void _computeChanges(value) {
    if (value is CollectionChangeRecord) {
      _computeCollectionChanges(value, _first);
    } else if (value is MapChangeRecord) {
      _computeMapChanges(value, _first);
    } else {
      if (value is String) {
        _currentSet..clear()..addAll(value.split(' '));
      } else if (value == null) {
        _currentSet.clear();
      } else {
        throw 'ng-class expects expression value to be List, Map or String, '
              'got $value';
      }
    }

    _first = false;
  }

  // todo(vicb) refactor once GH-774 gets fixed
  void _computeCollectionChanges(CollectionChangeRecord changes, bool first) {
    if (first) {
      changes.iterable.forEach((cls) {
        _currentSet.add(cls);
      });
    } else {
      changes.forEachAddition((CollectionChangeItem a) {
        _currentSet.add(a.item);
      });
      changes.forEachRemoval((CollectionChangeItem r) {
        _currentSet.remove(r.item);
      });
    }
  }

  // todo(vicb) refactor once GH-774 gets fixed
  _computeMapChanges(MapChangeRecord changes, first) {
    if (first) {
      changes.map.forEach((cls, active) {
        if (toBool(active)) _currentSet.add(cls);
      });
    } else {
      changes.forEachChange((MapKeyValue kv) {
        var cls = kv.key;
        var active = toBool(kv.currentValue);
        var wasActive = toBool(kv.previousValue);
        if (active != wasActive) {
          if (active) {
            _currentSet.add(cls);
          } else {
            _currentSet.remove(cls);
          }
        }
      });
      changes.forEachAddition((MapKeyValue kv) {
        if (toBool(kv.currentValue)) _currentSet.add(kv.key);
      });
      changes.forEachRemoval((MapKeyValue kv) {
        if (toBool(kv.previousValue)) _currentSet.remove(kv.key);
      });
    }
  }

  _applyChanges(index) {
    if (_mode == null || (index != null && index % 2 == _mode)) {
      _previousSet
          .where((cls) => cls != null)
          .forEach((cls) => _ngElement.removeClass(cls));
      _currentSet
          .where((cls) => cls != null)
          .forEach((cls) => _ngElement.addClass(cls));
    }

    _previousSet = _currentSet.toSet();
  }
}
