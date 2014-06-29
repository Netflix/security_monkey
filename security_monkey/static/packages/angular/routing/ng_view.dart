part of angular.routing;

/**
 * A directive that works with the [Router] and loads the template associated
 * with the current route.
 *
 *     <ng-view></ng-view>
 *
 * [NgViewDirective] can work with [NgViewDirective] to define nested views
 * for hierarchical routes. For example:
 *
 *     void initRoutes(Router router, RouteViewFactory views) {
 *       views.configure({
 *          'library': ngRoute(
 *              path: '/library',
 *              view: 'library.html',
 *              mount: {
 *                  'all': ngRoute(
 *                      path: '/all',
 *                      view: 'book_list.html'),
 *                   'book': ngRoute(
 *                      path: '/:bookId',
 *                      mount: {
 *                          'overview': ngRoute(
 *                              path: '/overview',
 *                              defaultRoute: true,
 *                              view: 'book_overview.html'),
 *                          'read': ngRoute(
 *                              path: '/read',
 *                              view: 'book_read.html'),
 *                      })
 *              })
 *       });
 *
 * index.html:
 *
 *     <ng-view></ng-view>
 *
 * library.html:
 *
 *     <div>
 *       <h1>Library!</h1>
 *
 *       <ng-view></ng-view>
 *     </div>
 *
 * book_list.html:
 *
 *     <ul>
 *       <li><a href="/library/12345/overview">Book 12345</a>
 *       <li><a href="/library/23456/overview">Book 23456</a>
 *     </ul>
 */
@Decorator(
    selector: 'ng-view',
    module: NgView.module)
class NgView implements DetachAware, RouteProvider {
  static final Module _module = new Module()
      ..bind(RouteProvider, toFactory: (i) => i.get(NgView));

  static Module module() => _module;

  final NgRoutingHelper _locationService;
  final ViewCache _viewCache;
  final Injector _injector;
  final Element _element;
  final Scope _scope;
  RouteHandle _route;

  View _view;
  Scope _childScope;
  Route _viewRoute;

  NgView(this._element, this._viewCache, Injector injector, Router router, this._scope)
      : _injector = injector,
        _locationService = injector.get(NgRoutingHelper)
  {
    RouteProvider routeProvider = injector.parent.get(NgView);
    _route = routeProvider != null ?
        routeProvider.route.newHandle() :
        router.root.newHandle();
    _locationService._registerPortal(this);
    _maybeReloadViews();
  }

  void _maybeReloadViews() {
    if (_route.isActive) _locationService._reloadViews(startingFrom: _route);
  }

  void detach() {
    _route.discard();
    _locationService._unregisterPortal(this);
  }

  void _show(_View viewDef, Route route, List<Module> modules) {
    assert(route.isActive);

    if (_viewRoute != null) return;
    _viewRoute = route;

    StreamSubscription _leaveSubscription;
    _leaveSubscription = route.onLeave.listen((_) {
      _leaveSubscription.cancel();
      _leaveSubscription = null;
      _viewRoute = null;
      _cleanUp();
    });

    var viewInjector = modules == null ?
        _injector :
        forceNewDirectivesAndFormatters(_injector, modules);

    var newDirectives = viewInjector.get(DirectiveMap);
    var viewFuture = viewDef.templateHtml != null ?
        new Future.value(_viewCache.fromHtml(viewDef.templateHtml, newDirectives)) :
        _viewCache.fromUrl(viewDef.template, newDirectives);
    viewFuture.then((viewFactory) {
      _cleanUp();
      _childScope = _scope.createChild(new PrototypeMap(_scope.context));
      _view = viewFactory(
          viewInjector.createChild([new Module()..bind(Scope, toValue: _childScope)]));
      _view.nodes.forEach((elm) => _element.append(elm));
    });
  }

  void _cleanUp() {
    if (_view == null) return;

    _view.nodes.forEach((node) => node.remove());
    _childScope.destroy();

    _view = null;
    _childScope = null;
  }

  Route get route => _viewRoute;

  String get routeName => _viewRoute.name;

  Map<String, String> get parameters {
    var res = <String, String>{};
    var p = _viewRoute;
    while (p != null) {
      res.addAll(p.parameters);
      p = p.parent;
    }
    return res;
  }
}


/**
 * Class that can be injected to retrieve information about the current route.
 * For example:
 *
 *     @Component(/* ... */)
 *     class MyComponent implement DetachAware {
 *       RouteHandle route;
 *
 *       MyComponent(RouteProvider routeProvider) {
 *         _loadFoo(routeProvider.parameters['fooId']);
 *         route = routeProvider.route.newHandle();
 *         route.onEnter.listen((RouteEvent e) {
 *           // Do something when the route is activated.
 *         });
 *         route.onLeave.listen((RouteEvent e) {
 *           // Do something when the route is de-activated.
 *           e.allowLeave(allDataSaved());
 *         });
 *       }
 *
 *       detach() {
 *         // The route handle must be discarded.
 *         route.discard();
 *       }
 *
 *       Future<bool> allDataSaved() {
 *         // Check that all data is saved and confirm with the user if needed.
 *       }
 *     }
 *
 * If user component is used outside of ng-view directive then
 * injected [RouteProvider] will be null.
 */
abstract class RouteProvider {

  /**
   * Returns [Route] for current view.
   */
  Route get route;

  /**
   * Returns the name of the current route.
   */
  String get routeName;

  /**
   * Returns parameters for this route.
   */
  Map<String, String> get parameters;
}
