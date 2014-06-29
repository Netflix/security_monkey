part of angular.directive;

/**
 * Fetches, compiles and includes an external Angular template/HTML.
 *
 * A new child [Scope] is created for the included DOM subtree.
 *
 * [NgInclude] provides only one small part of the power of
 * [Component].  Consider using directives and components instead as they
 * provide this feature as well as much more.
 *
 * Note: The browser's Same Origin Policy (<http://v.gd/5LE5CA>) and
 * Cross-Origin Resource Sharing (CORS) policy (<http://v.gd/nXoY8y>) restrict
 * whether the template is successfully loaded.  For example,
 * [NgInclude] won't work for cross-domain requests on all browsers and
 * for `file://` access on some browsers.
 */
@Decorator(
    selector: '[ng-include]',
    map: const {'ng-include': '@url'})
class NgInclude {

  final dom.Element element;
  final Scope scope;
  final ViewCache viewCache;
  final Injector injector;
  final DirectiveMap directives;

  View _view;
  Scope _scope;

  NgInclude(this.element, this.scope, this.viewCache, this.injector, this.directives);

  _cleanUp() {
    if (_view == null) return;

    _view.nodes.forEach((node) => node.remove);
    _scope.destroy();
    element.innerHtml = '';

    _view = null;
    _scope = null;
  }

  _updateContent(createView) {
    // create a new scope
    _scope = scope.createChild(new PrototypeMap(scope.context));
    _view = createView(injector.createChild([new Module()
        ..bind(Scope, toValue: _scope)]));

    _view.nodes.forEach((node) => element.append(node));
  }


  set url(value) {
    _cleanUp();
    if (value != null && value != '') {
      viewCache.fromUrl(value, directives).then(_updateContent);
    }
  }
}
