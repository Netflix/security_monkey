part of angular.mock;

/*
 * Use Probe directive to capture the Scope, Injector and Element from any DOM
 * location into root-scope. This is useful for testing to get a hold of
 * any directive.
 *
 *    <div some-directive probe="myProbe">..</div>
 *
 *    rootScope.myProbe.directive(SomeAttrDirective);
 */
@Decorator(selector: '[probe]')
class Probe implements DetachAware {
  final Scope scope;
  final Injector injector;
  final Element element;
  String _probeName;

  Probe(this.scope, this.injector, this.element) {
    _probeName = element.attributes['probe'];
    scope.rootScope.context[_probeName] = this;
  }

  void detach() {
    scope.rootScope.context[_probeName] = null;
  }

  /**
   * Retrieve a Directive at the current element.
   */
  directive(Type type) => injector.get(type);
}

