part of angular.routing;

/**
 * A factory of route to template bindings.
 */
class RouteViewFactory {
  NgRoutingHelper locationService;

  RouteViewFactory(this.locationService);

  Function call(String templateUrl) =>
      (RouteEnterEvent event) => _enterHandler(event, templateUrl);

  void _enterHandler(RouteEnterEvent event, String templateUrl,
                     {List<Module> modules, String templateHtml}) {
    locationService._route(event.route, templateUrl, fromEvent: true,
        modules: modules, templateHtml: templateHtml);
  }

  void configure(Map<String, NgRouteCfg> config) {
    _configure(locationService.router.root, config);
  }

  void _configure(Route route, Map<String, NgRouteCfg> config) {
    config.forEach((name, cfg) {
      var modulesCalled = false;
      List<Module> newModules;
      route.addRoute(
          name: name,
          path: cfg.path,
          defaultRoute: cfg.defaultRoute,
          enter: (RouteEnterEvent e) {
            if (cfg.view != null || cfg.viewHtml != null) {
              _enterHandler(e, cfg.view,
                  modules: newModules, templateHtml: cfg.viewHtml);
            }
            if (cfg.enter != null) {
              cfg.enter(e);
            }
          },
          preEnter: (RoutePreEnterEvent e) {
            if (cfg.modules != null && !modulesCalled) {
              modulesCalled = true;
              var modules = cfg.modules();
              if (modules is Future) {
                e.allowEnter(modules.then((List<Module> m) {
                  newModules = m;
                  return true;
                }));
              } else {
                newModules = modules;
              }
            }
            if (cfg.preEnter != null) {
              cfg.preEnter(e);
            }
          },
          preLeave: (RoutePreLeaveEvent e) {
            if (cfg.preLeave != null) {
              cfg.preLeave(e);
            }
          },
          leave: cfg.leave,
          mount: (Route mountRoute) {
            if (cfg.mount != null) {
              _configure(mountRoute, cfg.mount);
            }
          });
    });
  }
}

NgRouteCfg ngRoute({String path, String view, String viewHtml,
    Map<String, NgRouteCfg> mount, modules(), bool defaultRoute: false,
    RoutePreEnterEventHandler preEnter, RouteEnterEventHandler enter,
    RoutePreLeaveEventHandler preLeave, RouteLeaveEventHandler leave}) =>
        new NgRouteCfg(path: path, view: view, viewHtml: viewHtml, mount: mount,
            modules: modules, defaultRoute: defaultRoute, preEnter: preEnter,
            preLeave: preLeave, enter: enter, leave: leave);

class NgRouteCfg {
  final String path;
  final String view;
  final String viewHtml;
  final Map<String, NgRouteCfg> mount;
  final Function modules;
  final bool defaultRoute;
  final RouteEnterEventHandler enter;
  final RoutePreEnterEventHandler preEnter;
  final RoutePreLeaveEventHandler preLeave;
  final RouteLeaveEventHandler leave;

  NgRouteCfg({this.view, this.viewHtml, this.path, this.mount, this.modules,
      this.defaultRoute, this.enter, this.preEnter, this.preLeave, this.leave});
}

/**
 * An interface that must be implemented by the user of routing library and
 * should include the route initialization.
 *
 * The [init] method will be called by the framework once the router is
 * instantiated but before [NgBindRouteDirective] and [NgViewDirective].
 */
@Deprecated("use RouteInitializerFn instead")
abstract class RouteInitializer {
  void init(Router router, RouteViewFactory viewFactory);
}

/**
 * An typedef that must be implemented by the user of routing library and
 * should include the route initialization.
 *
 * The function will be called by the framework once the router is
 * instantiated but before [NgBindRouteDirective] and [NgViewDirective].
 */
typedef void RouteInitializerFn(Router router, RouteViewFactory viewFactory);

/**
 * A singleton helper service that handles routing initialization, global
 * events and view registries.
 */
@Injectable()
class NgRoutingHelper {
  final Router router;
  final Application _ngApp;
  final _portals = <NgView>[];
  final _templates = <String, _View>{};

  NgRoutingHelper(RouteInitializer initializer, Injector injector, this.router,
                  this._ngApp) {
    // TODO: move this to constructor parameters when di issue is fixed:
    // https://github.com/angular/di.dart/issues/40
    RouteInitializerFn initializerFn = injector.get(RouteInitializerFn);
    if (initializer == null && initializerFn == null) {
      window.console.error('No RouteInitializer implementation provided.');
      return;
    };

    if (initializerFn != null) {
      initializerFn(router, new RouteViewFactory(this));
    } else {
      initializer.init(router, new RouteViewFactory(this));
    }
    router.onRouteStart.listen((RouteStartEvent routeEvent) {
      routeEvent.completed.then((success) {
        if (success) {
          _portals.forEach((NgView p) => p._maybeReloadViews());
        }
      });
    });

    router.listen(appRoot: _ngApp.element);
  }

  void _reloadViews({Route startingFrom}) {
    var alreadyActiveViews = [];
    var activePath = router.activePath;
    if (startingFrom != null) {
      activePath = activePath.skip(_routeDepth(startingFrom));
    }
    for (Route route in activePath) {
      var viewDef = _templates[_routePath(route)];
      if (viewDef == null) continue;
      var templateUrl = viewDef.template;

      NgView view = _portals.lastWhere((NgView v) {
        return _routePath(route) != _routePath(v._route) &&
            _routePath(route).startsWith(_routePath(v._route));
      }, orElse: () => null);
      if (view != null && !alreadyActiveViews.contains(view)) {
        view._show(viewDef, route, viewDef.modules);
        alreadyActiveViews.add(view);
        break;
      }
    }
  }

  void _route(Route route, String template, {bool fromEvent, List<Module> modules,
      String templateHtml}) {
    _templates[_routePath(route)] = new _View(template, templateHtml, modules);
  }

  void _registerPortal(NgView ngView) {
    _portals.add(ngView);
  }

  void _unregisterPortal(NgView ngView) {
    _portals.remove(ngView);
  }
}

class _View {
  final String template;
  final String templateHtml;
  final List<Module> modules;

  _View(this.template, this.templateHtml, this.modules);
}

String _routePath(Route route) {
  final path = [];
  var p = route;
  while (p.parent != null) {
    path.insert(0, p.name);
    p = p.parent;
  }
  return path.join('.');
}

int _routeDepth(Route route) {
  var depth = 0;
  var p = route;
  while (p.parent != null) {
    depth++;
    p = p.parent;
  }
  return depth;
}
