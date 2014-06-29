part of route.client;

/**
 * A helper Router handle that scopes all route event subsriptions to it's
 * instance and provides an convinience [discard] method.
 */
class RouteHandle implements Route {
  Route _route;
  final StreamController<RoutePreEnterEvent> _onPreEnterController;
  final StreamController<RoutePreLeaveEvent> _onPreLeaveController;
  final StreamController<RouteEnterEvent> _onEnterController;
  final StreamController<RouteLeaveEvent> _onLeaveController;

  @override
  @Deprecated("use [onEnter] instead.")
  Stream<RouteEnterEvent> get onRoute => onEnter;
  @override
  Stream<RoutePreEnterEvent> get onPreEnter => _onPreEnterController.stream;
  @override
  Stream<RoutePreLeaveEvent> get onPreLeave => _onPreLeaveController.stream;
  @override
  Stream<RouteEnterEvent> get onEnter => _onEnterController.stream;
  @override
  Stream<RouteLeaveEvent> get onLeave => _onLeaveController.stream;

  StreamSubscription _onPreEnterSubscription;
  StreamSubscription _onPreLeaveSubscription;
  StreamSubscription _onEnterSubscription;
  StreamSubscription _onLeaveSubscription;
  List<RouteHandle> _childHandles = <RouteHandle>[];

  RouteHandle._new(this._route)
      : _onEnterController =
            new StreamController<RouteEnterEvent>.broadcast(sync: true),
        _onPreEnterController =
            new StreamController<RoutePreEnterEvent>.broadcast(sync: true),
        _onPreLeaveController =
            new StreamController<RoutePreLeaveEvent>.broadcast(sync: true),
        _onLeaveController =
            new StreamController<RouteLeaveEvent>.broadcast(sync: true) {
    _onEnterSubscription = _route.onEnter.listen(_onEnterController.add);
    _onPreEnterSubscription =
        _route.onPreEnter.listen(_onPreEnterController.add);
    _onPreLeaveSubscription =
        _route.onPreLeave.listen(_onPreLeaveController.add);
    _onLeaveSubscription = _route.onLeave.listen(_onLeaveController.add);
  }

  /// discards this handle.
  void discard() {
    _logger.finest('discarding handle for $_route');
    _onPreEnterSubscription.cancel();
    _onPreLeaveSubscription.cancel();
    _onEnterSubscription.cancel();
    _onLeaveSubscription.cancel();
    _onEnterController.close();
    _onLeaveController.close();
    _childHandles
        ..forEach((RouteHandle c) => c.discard())
        ..clear();
    _route = null;
  }

  /// Not supported. Overridden to throw an error.
  @override
  void addRoute({String name, Pattern path, bool defaultRoute: false,
      RouteEnterEventHandler enter, RoutePreEnterEventHandler preEnter,
      RoutePreLeaveEventHandler preLeave,RouteLeaveEventHandler leave,
      mount, dontLeaveOnParamChanges: false}) {
    throw new UnsupportedError('addRoute is not supported in handle');
  }

  @override
  @Deprecated("use [findRoute] instead.")
  Route getRoute(String routePath) => findRoute(routePath);

  @override
  Route findRoute(String routePath) {
    Route r = _assertState(() => _getHost(_route).findRoute(routePath));
    if (r == null) return null;
    var handle = r.newHandle();
    if (handle != null) _childHandles.add(handle);
    return handle;
  }

  /**
   * Create an return a new [RouteHandle] for this route.
   */
  @override
  RouteHandle newHandle() {
    _logger.finest('newHandle for $this');
    return new RouteHandle._new(_getHost(_route));
  }

  Route _getHost(Route r) {
    _assertState();
    if (r == null) throw new StateError('Oops?!');
    if ((r is Route) && (r is! RouteHandle)) return r;
    RouteHandle rh = r;
    return rh._getHost(rh._route);
  }

  dynamic _assertState([f()]) {
    if (_route == null) {
      throw new StateError('This route handle is already discated.');
    }
    return f == null ? null : f();
  }

  /// See [Route.isActive]
  @override
  bool get isActive => _route.isActive;

  /// See [Route.parameters]
  @override
  Map get parameters => _route.parameters;

  /// See [Route.path]
  @override
  UrlMatcher get path => _route.path;

  /// See [Route.name]
  @override
  String get name => _route.name;

  /// See [Route.parent]
  @override
  Route get parent => _route.parent;

  /// See [Route.dontLeaveOnParamChanges]
  @override
  bool get dontLeaveOnParamChanges => _route.dontLeaveOnParamChanges;
}
