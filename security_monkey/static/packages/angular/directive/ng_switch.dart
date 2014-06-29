part of angular.directive;

/**
 * The ngSwitch directive is used to conditionally swap DOM structure on your
 * template based on a scope expression. Elements within ngSwitch but without
 * ngSwitchWhen or ngSwitchDefault directives will be preserved at the location
 * as specified in the template.
 *
 * The directive itself works similar to ngInclude, however, instead of
 * downloading template code (or loading it from the template cache), ngSwitch
 * simply choses one of the nested elements and makes it visible based on which
 * element matches the value obtained from the evaluated expression. In other
 * words, you define a container element (where you place the directive), place
 * an expression on the **ng-switch="..." attribute**, define any inner elements
 * inside of the directive and place a when attribute per element. The when
 * attribute is used to inform ngSwitch which element to display when the on
 * expression is evaluated. If a matching expression is not found via a when
 * attribute then an element with the default attribute is displayed.
 *
 * ## Example:
 *
 *     <ANY ng-switch="expression">
 *       <ANY ng-switch-when="matchValue1">...</ANY>
 *       <ANY ng-switch-when="matchValue2">...</ANY>
 *       <ANY ng-switch-default>...</ANY>
 *     </ANY>
 *
 * On child elements add:
 *
 * * `ngSwitchWhen`: the case statement to match against. If match then this
 *   case will be displayed. If the same match appears multiple times, all the
 *   elements will be displayed.
 * * `ngSwitchDefault`: the default case when no other case match. If there
 *   are multiple default cases, all of them will be displayed when no other
 *   case match.
 *
 * ## Example:
 *
 *     <div>
 *       <button ng-click="selection='settings'">Show Settings</button>
 *       <button ng-click="selection='home'">Show Home Span</button>
 *       <button ng-click="selection=''">Show default</button>
 *       <tt>selection={{selection}}</tt>
 *       <hr/>
 *       <div ng-switch="selection">
 *           <div ng-switch-when="settings">Settings Div</div>
 *           <div ng-switch-when="home">Home Span</div>
 *           <div ng-switch-default>default</div>
 *       </div>
 *     </div>
 */
@Decorator(
    selector: '[ng-switch]',
    map: const {
      'ng-switch': '=>value',
      'change': '&onChange'
    },
    visibility: Directive.DIRECT_CHILDREN_VISIBILITY)
class NgSwitch {
  Map<String, List<_Case>> cases = new Map<String, List<_Case>>();
  List<_ViewScopePair> currentViews = <_ViewScopePair>[];
  Function onChange;
  final Scope scope;

  NgSwitch(this.scope) {
    cases['?'] = <_Case>[];
  }

  addCase(String value, ViewPort anchor, BoundViewFactory viewFactory) {
    cases.putIfAbsent(value, () => <_Case>[]);
    cases[value].add(new _Case(anchor, viewFactory));
  }

  set value(val) {
    currentViews
        ..forEach((_ViewScopePair pair) {
          pair.port.remove(pair.view);
          pair.scope.destroy();
        })
        ..clear();

    val = '!$val';
    (cases.containsKey(val) ? cases[val] : cases['?'])
        .forEach((_Case caze) {
          Scope childScope = scope.createChild(new PrototypeMap(scope.context));
          var view = caze.viewFactory(childScope);
          caze.anchor.insert(view);
          currentViews.add(new _ViewScopePair(view, caze.anchor,
            childScope));
        });
    if (onChange != null) {
      onChange();
    }
  }
}

class _ViewScopePair {
  final View view;
  final ViewPort port;
  final Scope scope;

  _ViewScopePair(this.view, this.port, this.scope);
}

class _Case {
  final ViewPort anchor;
  final BoundViewFactory viewFactory;

  _Case(this.anchor, this.viewFactory);
}

@Decorator(
    selector: '[ng-switch-when]',
    children: Directive.TRANSCLUDE_CHILDREN,
    map: const {'.': '@value'})
class NgSwitchWhen {
  final NgSwitch ngSwitch;
  final ViewPort port;
  final BoundViewFactory viewFactory;
  final Scope scope;

  NgSwitchWhen(this.ngSwitch, this.port, this.viewFactory, this.scope);

  set value(String value) => ngSwitch.addCase('!$value', port, viewFactory);
}

@Decorator(
    children: Directive.TRANSCLUDE_CHILDREN,
    selector: '[ng-switch-default]')
class NgSwitchDefault {

  NgSwitchDefault(NgSwitch ngSwitch, ViewPort port,
                  BoundViewFactory viewFactory, Scope scope) {
    ngSwitch.addCase('?', port, viewFactory);
  }
}
