// Copyright (c) 2013, the Dart project authors.  Please see the AUTHORS file
// for details. All rights reserved. Use of this source code is governed by a
// BSD-style license that can be found in the LICENSE file.

library route.client;

import 'dart:async';
import 'dart:html';
import 'dart:math';

import 'package:logging/logging.dart';

import 'src/utils.dart';

import 'link_matcher.dart';
import 'click_handler.dart';
import 'url_matcher.dart';
export 'url_matcher.dart';
import 'url_template.dart';

part 'route_handle.dart';


final _logger = new Logger('route');
const _PATH_SEPARATOR = '.';

typedef void RoutePreEnterEventHandler(RoutePreEnterEvent event);
typedef void RouteEnterEventHandler(RouteEnterEvent event);
typedef void RoutePreLeaveEventHandler(RoutePreLeaveEvent event);
typedef void RouteLeaveEventHandler(RouteLeaveEvent event);

/**
 * [Route] represents a node in the route tree.
 */
abstract class Route {
  /**
   * Name of the route. Used when querying routes.
   */
  String get name;

  /**
   * A path fragment [UrlMatcher] for this route.
   */
  UrlMatcher get path;

  /**
   * Parent route in the route tree.
   */
  Route get parent;

  /**
   * Indicates whether this route is currently active. Root route is always
   * active.
   */
  bool get isActive;

  /**
   * Returns parameters for the currently active route. If the route is not
   * active the getter returns null.
   */
  Map get parameters;

  /**
   * Whether to trigger the leave event when only the parameters change.
   */
  bool get dontLeaveOnParamChanges;

  /**
   * Returns a stream of [RouteEnterEvent] events. The [RouteEnterEvent] event
   * is fired when route has already been made active, but before subroutes
   * are entered. The event starts at the root and propagates from parent to
   * child routes.
   */
  @Deprecated("use [onEnter] instead.")
  Stream<RouteEnterEvent> get onRoute;

  /**
   * Returns a stream of [RoutePreEnterEvent] events. The [RoutePreEnterEvent]
   * event is fired when the route is matched during the routing, but before
   * any previous routes were left, or any new routes were entered. The event
   * starts at the root and propagates from parent to child routes.
   *
   * At this stage it's possible to veto entering of the route by calling
   * [RoutePreEnterEvent.allowEnter] with a [Future] returns a boolean value
   * indicating whether enter is permitted (true) or not (false).
   */
  Stream<RoutePreEnterEvent> get onPreEnter;

  /**
   * Returns a stream of [RoutePreLeaveEvent] events. The [RoutePreLeaveEvent]
   * event is fired when the route is NOT matched during the routing, but before
   * any routes are actually left, or any new routes were entered.
   *
   * At this stage it's possible to veto leaving of the route by calling
   * [RoutePreLeaveEvent.allowLeave] with a [Future] returns a boolean value
   * indicating whether enter is permitted (true) or not (false).
   */
  Stream<RoutePreLeaveEvent> get onPreLeave;

  /**
   * Returns a stream of [RouteLeaveEvent] events. The [RouteLeaveEvent]
   * event is fired when the route is being left. The event starts at the leaf
   * route and propagates from child to parent routes.
   *
   * At this stage it's possible to veto leaving of the route by calling
   * [RouteLeaveEvent.allowLeave] with a [Future] returns a boolean value
   * indicating whether leave is permitted (true) or not (false).
   *
   * Note: that once child routes have been notified of the leave they will not
   * be notified of the subsequent veto by any parent route. See:
   * https://github.com/angular/route.dart/issues/28
   */
  Stream<RouteLeaveEvent> get onLeave;

  /**
   * Returns a stream of [RouteEnterEvent] events. The [RouteEnterEvent] event
   * is fired when route has already been made active, but before subroutes
   * are entered.  The event starts at the root and propagates from parent
   * to child routes.
   */
  Stream<RouteEnterEvent> get onEnter;

  void addRoute({String name, Pattern path, bool defaultRoute: false,
        RouteEnterEventHandler enter, RoutePreEnterEventHandler preEnter,
        RoutePreLeaveEventHandler preLeave, RouteLeaveEventHandler leave,
        mount, dontLeaveOnParamChanges: false});

  /**
   * Queries sub-routes using the [routePath] and returns the matching [Route].
   *
   * [routePath] is a dot-separated list of route names. Ex: foo.bar.baz, which
   * means that current route should contain route named 'foo', the 'foo' route
   * should contain route named 'bar', and so on.
   *
   * If no match is found then [:null:] is returned.
   */
  @Deprecated("use [findRoute] instead.")
  Route getRoute(String routePath);

  /**
   * Queries sub-routes using the [routePath] and returns the matching [Route].
   *
   * [routePath] is a dot-separated list of route names. Ex: foo.bar.baz, which
   * means that current route should contain route named 'foo', the 'foo' route
   * should contain route named 'bar', and so on.
   *
   * If no match is found then [:null:] is returned.
   */
  Route findRoute(String routePath);

  /**
   * Create an return a new [RouteHandle] for this route.
   */
  RouteHandle newHandle();

  String toString() => '[Route: $name]';
}

/**
 * Route is a node in the tree of routes. The edge leading to the route is
 * defined by path.
 */
class RouteImpl extends Route {
  @override
  final String name;
  @override
  final UrlMatcher path;
  @override
  final RouteImpl parent;

  final _routes = <String, RouteImpl>{};
  final StreamController<RouteEnterEvent> _onEnterController;
  final StreamController<RoutePreEnterEvent> _onPreEnterController;
  final StreamController<RoutePreLeaveEvent> _onPreLeaveController;
  final StreamController<RouteLeaveEvent> _onLeaveController;
  RouteImpl _defaultRoute;
  RouteImpl _currentRoute;
  RouteEvent _lastEvent;
  @override
  final bool dontLeaveOnParamChanges;

  @override
  @Deprecated("use [onEnter] instead.")
  Stream<RouteEvent> get onRoute => onEnter;
  @override
  Stream<RouteEvent> get onPreEnter => _onPreEnterController.stream;
  @override
  Stream<RouteEvent> get onPreLeave => _onPreLeaveController.stream;
  @override
  Stream<RouteEvent> get onLeave => _onLeaveController.stream;
  @override
  Stream<RouteEvent> get onEnter => _onEnterController.stream;

  RouteImpl._new({this.name, this.path, this.parent,
                 this.dontLeaveOnParamChanges: false})
      : _onEnterController =
            new StreamController<RouteEnterEvent>.broadcast(sync: true),
        _onPreEnterController =
            new StreamController<RoutePreEnterEvent>.broadcast(sync: true),
        _onPreLeaveController =
            new StreamController<RoutePreLeaveEvent>.broadcast(sync: true),
        _onLeaveController =
            new StreamController<RouteLeaveEvent>.broadcast(sync: true);

  @override
  void addRoute({String name, Pattern path, bool defaultRoute: false,
      RouteEnterEventHandler enter, RoutePreEnterEventHandler preEnter,
      RoutePreLeaveEventHandler preLeave, RouteLeaveEventHandler leave,
      mount, dontLeaveOnParamChanges: false}) {
    if (name == null) {
      throw new ArgumentError('name is required for all routes');
    }
    if (name.contains(_PATH_SEPARATOR)) {
      throw new ArgumentError('name cannot contain dot.');
    }
    if (_routes.containsKey(name)) {
      throw new ArgumentError('Route $name already exists');
    }

    var matcher = path is UrlMatcher ? path : new UrlTemplate(path.toString());

    var route = new RouteImpl._new(name: name, path: matcher, parent: this,
        dontLeaveOnParamChanges: dontLeaveOnParamChanges);

    route..onPreEnter.listen(preEnter)
         ..onPreLeave.listen(preLeave)
         ..onEnter.listen(enter)
         ..onLeave.listen(leave);

    if (mount != null) {
      if (mount is Function) {
        mount(route);
      } else if (mount is Routable) {
        mount.configureRoute(route);
      }
    }

    if (defaultRoute) {
      if (_defaultRoute != null) {
        throw new StateError('Only one default route can be added.');
      }
      _defaultRoute = route;
    }
    _routes[name] = route;
  }

  @override
  Route getRoute(String routePath) => findRoute(routePath);

  @override
  Route findRoute(String routePath) {
    var routeName = routePath.split(_PATH_SEPARATOR).first;
    if (!_routes.containsKey(routeName)) {
      _logger.warning('Invalid route name: $routeName $_routes');
      return null;
    }
    var routeToGo = _routes[routeName];
    var childPath = routePath.substring(routeName.length);
    return childPath.isEmpty ? routeToGo :
        routeToGo.getRoute(childPath.substring(1));
  }

  String _getHead(String tail, Map queryParams) {
    if (parent == null) return tail;
    if (parent._currentRoute == null) {
      throw new StateError('Router $parent has no current router.');
    }
    _populateQueryParams(parent._currentRoute._lastEvent.parameters,
        parent._currentRoute, queryParams);
    return parent._getHead(parent._currentRoute._reverse(tail), queryParams);
  }

  String _getTailUrl(String routePath, Map parameters, Map queryParams) {
    var routeName = routePath.split('.').first;
    if (!_routes.containsKey(routeName)) {
      throw new StateError('Invalid route name: $routeName');
    }
    var routeToGo = _routes[routeName];
    var tail = '';
    var childPath = routePath.substring(routeName.length);
    if (childPath.isNotEmpty) {
      tail = routeToGo._getTailUrl(
          childPath.substring(1), parameters, queryParams);
    }
    _populateQueryParams(parameters, routeToGo, queryParams);
    return routeToGo.path.reverse(
        parameters: _joinParams(parameters, routeToGo._lastEvent), tail: tail);
  }

  void _populateQueryParams(Map parameters, Route route, Map queryParams) {
    parameters.keys.forEach((String prefixedKey) {
      if (prefixedKey.startsWith('${route.name}.')) {
        var key = prefixedKey.substring('${route.name}.'.length);
        if (!route.path.urlParameterNames().contains(key)) {
          queryParams[prefixedKey] = parameters[prefixedKey];
        }
      }
    });
  }

  Map _joinParams(Map parameters, RouteEvent lastEvent) => lastEvent == null
      ? parameters
      : new Map.from(lastEvent.parameters)..addAll(parameters);

  /**
   * Returns a URL for this route. The tail (url generated by the child path)
   * will be passes to the UrlMatcher to be properly appended in the
   * right place.
   */
  String _reverse(String tail) =>
      path.reverse(parameters: _lastEvent.parameters, tail: tail);

  /**
   * Create an return a new [RouteHandle] for this route.
   */
  @override
  RouteHandle newHandle() {
    _logger.finest('newHandle for $this');
    return new RouteHandle._new(this);
  }

  /**
   * Indicates whether this route is currently active. Root route is always
   * active.
   */
  @override
  bool get isActive =>
      parent == null ? true : identical(parent._currentRoute, this);

  /**
   * Returns parameters for the currently active route. If the route is not
   * active the getter returns null.
   */
  @override
  Map get parameters {
    if (isActive) {
      return _lastEvent == null ? {} : new Map.from(_lastEvent.parameters);
    }
    return null;
  }
}

/**
 * Route enter or leave event.
 */
abstract class RouteEvent {
  final String path;
  final Map parameters;
  final Route route;

  RouteEvent(this.path, this.parameters, this.route);
}

class RoutePreEnterEvent extends RouteEvent {
  final _allowEnterFutures = <Future<bool>>[];

  RoutePreEnterEvent(path, parameters, route)  : super(path, parameters, route);

  RoutePreEnterEvent._fromMatch(_Match m)
      : this(m.urlMatch.tail, m.urlMatch.parameters, m.route);

  /**
   * Can be called on enter with the future which will complete with a boolean
   * value allowing ([:true:]) or disallowing ([:false:]) the current
   * navigation.
   */
  void allowEnter(Future<bool> allow) {
    _allowEnterFutures.add(allow);
  }
}

class RouteEnterEvent extends RouteEvent {

  RouteEnterEvent(path, parameters, route)  : super(path, parameters, route);

  RouteEnterEvent._fromMatch(_Match m)
      : this(m.urlMatch.match, m.urlMatch.parameters, m.route);
}

class RouteLeaveEvent extends RouteEvent {
  RouteLeaveEvent(path, parameters, route)  : super(path, parameters, route);

  RouteLeaveEvent _clone() => new RouteLeaveEvent(path, parameters, route);
}

class RoutePreLeaveEvent extends RouteEvent {
  final _allowLeaveFutures = <Future<bool>>[];

  RoutePreLeaveEvent(path, parameters, route)  : super(path, parameters, route);

  /**
   * Can be called with the future which will complete with a boolean
   * value allowing ([:true:]) or disallowing ([:false:]) the current
   * navigation.
   */
  void allowLeave(Future<bool> allow) {
    _allowLeaveFutures.add(allow);
  }

  RoutePreLeaveEvent _clone() => new RoutePreLeaveEvent(path, parameters, route);
}

/**
 * Event emitted when routing starts.
 */
class RouteStartEvent {
  /**
   * URI that was passed to [Router.route].
   */
  final String uri;

  /**
   * Future that completes to a boolean value of whether the routing was
   * successful.
   */
  final Future<bool> completed;

  RouteStartEvent._new(this.uri, this.completed);
}

abstract class Routable {
  void configureRoute(Route router);
}

/**
 * Stores a set of [UrlPattern] to [Handler] associations and provides methods
 * for calling a handler for a URL path, listening to [Window] history events,
 * and creating HTML event handlers that navigate to a URL.
 */
class Router {
  final bool _useFragment;
  final Window _window;
  final Route root;
  final _onRouteStart =
      new StreamController<RouteStartEvent>.broadcast(sync: true);
  final bool sortRoutes;
  bool _listen = false;
  WindowClickHandler _clickHandler;

  /**
   * [useFragment] determines whether this Router uses pure paths with
   * [History.pushState] or paths + fragments and [Location.assign]. The default
   * value is null which then determines the behavior based on
   * [History.supportsState].
   */
  Router({bool useFragment, Window windowImpl, bool sortRoutes: true,
         RouterLinkMatcher linkMatcher, WindowClickHandler clickHandler})
      : this._init(null, useFragment: useFragment, windowImpl: windowImpl,
          sortRoutes: sortRoutes, linkMatcher: linkMatcher, clickHandler: clickHandler);


  Router._init(Router parent, {bool useFragment, Window windowImpl,
      this.sortRoutes, RouterLinkMatcher linkMatcher,
      WindowClickHandler clickHandler})
      : _useFragment = (useFragment == null)
            ? !History.supportsState
            : useFragment,
        _window = (windowImpl == null) ? window : windowImpl,
        root = new RouteImpl._new() {
    var lm = linkMatcher == null ? new DefaultRouterLinkMatcher() : linkMatcher;
    _clickHandler = clickHandler == null ?
        new DefaultWindowClickHandler(lm, this, _useFragment, _window, _normalizeHash) : clickHandler;
  }

  /**
   * A stream of route calls.
   */
  Stream<RouteStartEvent> get onRouteStart => _onRouteStart.stream;

  /**
   * Finds a matching [Route] added with [addRoute], parses the path
   * and invokes the associated callback.
   *
   * This method does not perform any navigation, [go] should be used for that.
   * This method is used to invoke a handler after some other code navigates the
   * window, such as [listen].
   */
  Future<bool> route(String path, {Route startingFrom}) {
    var future = _route(path, startingFrom);
    _onRouteStart.add(new RouteStartEvent._new(path, future));
    return future;
  }

  Future<bool> _route(String path, Route startingFrom) {
    var baseRoute = startingFrom == null ? root : _dehandle(startingFrom);
    _logger.finest('route $path $baseRoute');
    var treePath = _matchingTreePath(path, baseRoute);
    var mustLeave = activePath;
    var leaveBase = root;
    for (var i = 0, ll = min(activePath.length, treePath.length); i < ll; i++) {
      if (mustLeave.first == treePath[i].route &&
          (treePath[i].route.dontLeaveOnParamChanges ||
              !_paramsChanged(treePath[i].route, treePath[i].urlMatch))) {
        mustLeave = mustLeave.skip(1);
        leaveBase = leaveBase._currentRoute;
      } else {
        break;
      }
    }
    return _preLeave(path, mustLeave, treePath, leaveBase);
  }

  Future<bool> _preLeave(String path, Iterable<Route> mustLeave,
      List<_Match> treePath, Route leaveBase) {
    // Reverse the list to ensure child is left before the parent.
    mustLeave = mustLeave.toList().reversed;

    var preLeaving = <Future<bool>>[];
    mustLeave.forEach((toLeave) {
      var event = new RoutePreLeaveEvent('', {}, toLeave);
      toLeave._onPreLeaveController.add(event);
      preLeaving.addAll(event._allowLeaveFutures);
    });
    return Future.wait(preLeaving).then((List<bool> results) {
      if (!results.any((r) => r == false)) {
        _leave(mustLeave, leaveBase);

        return _preEnter(path, treePath);
      }
      return new Future.value(false);
    });
  }

  void _leave(Iterable<Route> mustLeave, Route leaveBase) {
    mustLeave.forEach((toLeave) {
      var event = new RouteLeaveEvent('', {}, toLeave);
      toLeave._onLeaveController.add(event);
    });
    if (!mustLeave.isEmpty) {
      _unsetAllCurrentRoutesRecursively(leaveBase);
    }
  }

  void _unsetAllCurrentRoutesRecursively(RouteImpl r) {
    if (r._currentRoute != null) {
      _unsetAllCurrentRoutesRecursively(r._currentRoute);
      r._currentRoute = null;
    }
  }

  Future<bool> _preEnter(String path, List<_Match> treePath) {
    var toEnter = treePath;
    var tail = path;
    var enterBase = root;
    for (var i = 0, ll = min(toEnter.length, activePath.length); i < ll; i++) {
      if (toEnter.first.route == activePath[i] &&
          !_paramsChanged(activePath[i], treePath[i].urlMatch)) {
        tail = treePath[i].urlMatch.tail;
        toEnter = toEnter.skip(1);
        enterBase = enterBase._currentRoute;
      } else {
        break;
      }
    }
    if (toEnter.isEmpty) {
      return new Future.value(true);
    }

    var preEnterFutures = <Future<bool>>[];
    toEnter.forEach((_Match matchedRoute) {
      var preEnterEvent = new RoutePreEnterEvent._fromMatch(matchedRoute);
      matchedRoute.route._onPreEnterController.add(preEnterEvent);
      preEnterFutures.addAll(preEnterEvent._allowEnterFutures);
    });
    return Future.wait(preEnterFutures).then((List<bool> results) {
      if (!results.any((v) => v == false)) {
        _enter(enterBase, toEnter, tail);
        return new Future.value(true);
      }
      return new Future.value(false);
    });
  }

  _enter(RouteImpl startingFrom, Iterable<_Match> treePath, String path) {
    var base = startingFrom;
    treePath.forEach((_Match matchedRoute) {
      var event = new RouteEnterEvent._fromMatch(matchedRoute);
      base._currentRoute = matchedRoute.route;
      base._currentRoute._lastEvent = event;
      matchedRoute.route._onEnterController.add(event);
      base = matchedRoute.route;
    });
  }

  List _matchingRoutes(String path, RouteImpl baseRoute) {
    var routes = baseRoute._routes.values
        .where((r) => r.path.match(path) != null)
        .toList();

    return sortRoutes ?
        (routes..sort((r1, r2) => r1.path.compareTo(r2.path))) : routes;
  }

  List<_Match> _matchingTreePath(String path, RouteImpl baseRoute) {
    final treePath = <_Match>[];
    Route matchedRoute;
    do {
      matchedRoute = null;
      List matchingRoutes = _matchingRoutes(path, baseRoute);
      if (matchingRoutes.isNotEmpty) {
        if (matchingRoutes.length > 1) {
          _logger.warning("More than one route matches $path $matchingRoutes");
        }
        matchedRoute = matchingRoutes.first;
      } else {
        if (baseRoute._defaultRoute != null) {
          matchedRoute = baseRoute._defaultRoute;
        }
      }
      if (matchedRoute != null) {
        var match = _getMatch(matchedRoute, path);
        treePath.add(new _Match(matchedRoute, match));
        baseRoute = matchedRoute;
        path = match.tail;
      }
    } while (matchedRoute != null);
    return treePath;
  }

  bool _paramsChanged(RouteImpl route, UrlMatch match) {
    var lastEvent = route._lastEvent;
    return lastEvent == null || lastEvent.path != match.match ||
        !mapsShallowEqual(lastEvent.parameters, match.parameters);
  }

  /// Navigates to a given relative route path, and parameters.
  Future go(String routePath, Map parameters,
            {Route startingFrom, bool replace: false}) {
    var queryParams = {};
    var baseRoute = startingFrom == null ? this.root : _dehandle(startingFrom);
    var newTail = baseRoute._getTailUrl(routePath, parameters, queryParams) +
        _buildQuery(queryParams);
    String newUrl = baseRoute._getHead(newTail, queryParams);
    _logger.finest('go $newUrl');
    return route(newTail, startingFrom: baseRoute).then((success) {
      if (success) _go(newUrl, null, replace);
      return success;
    });
  }

  /// Returns an absolute URL for a given relative route path and parameters.
  String url(String routePath, {Route startingFrom, Map parameters}) {
    var baseRoute = startingFrom == null ? this.root : _dehandle(startingFrom);
    parameters = parameters == null ? {} : parameters;
    var queryParams = {};
    var tail = baseRoute._getTailUrl(routePath, parameters, queryParams);
    return (_useFragment ? '#' : '') + baseRoute._getHead(tail, queryParams) +
        _buildQuery(queryParams);
  }

  String _buildQuery(Map queryParams) {
    if (queryParams.isEmpty) return '';
    var query = queryParams.keys.map((key) =>
        '$key=${Uri.encodeComponent(queryParams[key])}').join('&');
    return '?$query';
  }

  Route _dehandle(Route r) => r is RouteHandle ? r._getHost(r): r;

  UrlMatch _getMatch(Route route, String path) {
    var match = route.path.match(path);
    // default route
    if (match == null) return new UrlMatch('', '', {});
    match.parameters.addAll(_parseQuery(route, path));
    return match;
  }

  Map _parseQuery(Route route, String path) {
    var params = {};
    if (path.indexOf('?') == -1) return params;
    var queryStr = path.substring(path.indexOf('?') + 1);
    queryStr.split('&').forEach((String keyValPair) {
      List<String> keyVal = _parseKeyVal(keyValPair);
      if (keyVal[0].startsWith('${route.name}.')) {
        var key = keyVal[0].substring('${route.name}.'.length);
        if (key.isNotEmpty) params[key] = Uri.decodeComponent(keyVal[1]);
      }
    });
    return params;
  }

  List<String> _parseKeyVal(kvPair) {
    if (kvPair.isEmpty) {
      return const ['', ''];
    }
    var splitPoint = kvPair.indexOf('=');

    return (splitPoint == -1) ?
        [kvPair, '']
        : [kvPair.substring(0, splitPoint), kvPair.substring(splitPoint + 1)];
  }

  /**
   * Listens for window history events and invokes the router. On older
   * browsers the hashChange event is used instead.
   */
  void listen({bool ignoreClick: false, Element appRoot}) {
    _logger.finest('listen ignoreClick=$ignoreClick');
    if (_listen) throw new StateError('listen can only be called once');
    _listen = true;
    if (_useFragment) {
      _window.onHashChange.listen((_) {
        route(_normalizeHash(_window.location.hash)).then((allowed) {
          // if not allowed, we need to restore the browser location
          if (!allowed) _window.history.back();
        });
      });
      route(_normalizeHash(_window.location.hash));
    } else {
      String getPath() =>
          '${_window.location.pathname}${_window.location.hash}';

      _window.onPopState.listen((_) {
        route(getPath()).then((allowed) {
          // if not allowed, we need to restore the browser location
          if (!allowed) _window.history.back();
        });
      });
      route(getPath());
    }
    if (!ignoreClick) {
      if (appRoot == null) appRoot = _window.document.documentElement;
      _logger.finest('listen on win');
      appRoot.onClick
          .where((MouseEvent e) => !(e.ctrlKey || e.metaKey || e.shiftKey))
          .listen(_clickHandler);
    }
  }

  String _normalizeHash(String hash) => hash.isEmpty ? '' : hash.substring(1);

  /**
   * Navigates the browser to the path produced by [url] with [args] by calling
   * [History.pushState], then invokes the handler associated with [url].
   *
   * On older browsers [Location.assign] is used instead with the fragment
   * version of the UrlPattern.
   */
  Future<bool> gotoUrl(String url) =>
      route(url).then((success) {
        if (success) _go(url, null, false);
      });

  void _go(String path, String title, bool replace) {
    if (_useFragment) {
      if (replace) {
        _window.location.replace('#$path');
      } else {
        _window.location.assign('#$path');
      }
      if (title != null) {
        (_window.document as HtmlDocument).title = title;
      }
    } else {
      if (title == null) {
        title = _window.document.title;
      }
      if (replace) {
        _window.history.replaceState(null, title, path);
      } else {
        _window.history.pushState(null, title, path);
      }
    }
  }

  /**
   * Returns the current active route path in the route tree.
   * Excludes the root path.
   */
  List<Route> get activePath {
    var res = <RouteImpl>[];
    var route = root;
    while (route._currentRoute != null) {
      route = route._currentRoute;
      res.add(route);
    }
    return res;
  }

  /**
   * A shortcut for router.root.findRoute().
   */
  Route findRoute(String routePath) => root.findRoute(routePath);
}

class _Match {
  final RouteImpl route;
  final UrlMatch urlMatch;

  _Match(this.route, this.urlMatch);

  toString() => route.toString();
}
