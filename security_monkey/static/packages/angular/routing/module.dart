/**
 * Route configuration for single-page applications.
 *
 * The [routing] library makes it easier to build large single-page
 * applications. The library lets you map the browser address bar to semantic
 * structure of your application and keeps them in sync.
 *
 * Angular uses the [route_hierarchical] package to define application routes
 * and to provide custom tools to make it easier to use routing with Angular
 * templates.
 *
 * Let's consider a simple recipe book application. The application might have
 * the following pages:
 *
 *   * recipes list/search
 *   * add new recipe
 *   * view recipe
 *   * edit recipe
 *
 * Each of those pages can be represented by an address:
 *
 *   * `/recipes`
 *   * `/addRecipe`
 *   * `/recipe/:recipeId/view`
 *   * `/recipe/:recipeId/edit`
 *
 * Let's try to define those routes in Angular. To get started we need to
 * provide an implementation of [RouteInitializerFn] function.
 *
 *      void initRoutes(Router router, RouteViewFactory view) {
 *        // define routes here.
 *      }
 *
 *      var module = new Module()
 *          ..bind(RouteInitializerFn, toValue: initRoutes);
 *
 *  Let's see how we could define our routes using the routing framework:
 *
 *      void initRoutes(Router router, RouteViewFactory views) {
 *        views.configure({
 *            'recipes': ngRoute(path: '/recipes', view: 'recipes.html'),
 *            'addRecipe': ngRoute(path: '/addRecipe', view: 'addRecipe.html'),
 *            'viewRecipe': ngRoute(path: '/recipe/:recipeId/view', view: 'viewRecipe.html'),
 *            'editRecipe': ngRoute(path: '/recipe/:recipeId/edit', view: 'editRecipe.html)
 *        });
 *      }
 *
 *  We defined 4 routes and for each route we set views (templates) to be
 *  displayed when that route is "entered". For example, when the browser URL
 *  is set to `/recipes`, the `recipes.html` template will be displayed.
 *
 *  You have to tell Angular where to load views by putting `<ng-view>` tag in
 *  you template.
 *
 *  Notice that `viewRecipe` and `editRecipe` route paths have `recipeId`
 *  parameter in them. We need to be able to get hold of that parameter in
 *  order to know which recipe to load. Let's consider the following
 *  `viewRecipe.html`.
 *
 *      <view-recipe></view-recipe>
 *
 *  The template contains a custom `view-recipe` component that handles
 *  displaying the recipe. Now, our `view-recipe` can inject [RouteProvider]
 *  to get hold of the route and its parameters. It might look like this:
 *
 *      @Component(...)
 *      class ViewRecipe {
 *        ViewRecipe(RouteProvider routeProvider) {
 *          String recipeId = routeProvider.parameters['recipeId'];
 *          _loadRecipe(recipeId);
 *        }
 *      }
 *
 *  [RouteProvider] and [Route] can be used to control navigation, specifically,
 *  leaving of the route. For example, let's consider "edit recipe" component:
 *
 *      @Component(...)
 *      class EditRecipe implements DetachAware {
 *        RouteHandle route;
 *        EditRecipe(RouteProvider routeProvider) {
 *          RouteHandle route = routeProvider.route.newHandle();
 *          _loadRecipe(route);
 *          route.onLeave.listen((RouteEvent event) {
 *            event.allowLeave(_checkIfOkToLeave());
 *          });
 *        }
 *
 *        /// Check if the editor has unsaved contents and if necessary ask
 *        /// the user if OK to leave this page.
 *        Future<bool> _checkIfOkToLeave() {/* ... */}
 *
 *        detach() {
 *          route.discard();
 *        }
 *      }
 *
 *  [Route.onLeave] event is triggered when the browser is routed from an
 *  active route to a different route. The active route can delay and
 *  potentially veto the navigation by passing a [Future<bool>] to
 *  [RouteEvent.allowLeave].
 *
 *  Notice that we create a [RouteHandle] for our route. [RouteHandle] are
 *  a convenient wrapper around [Route] that makes unsubscribing route events
 *  easier. For example, notice that we didn't need to manually call
 *  [StreamSubscription.cancel] for subscription to [Route.onLeave]. Calling
 *  [RouteHandle.discard] unsubscribes all listeners created for the handle.
 *
 * ## Hierarchical Routes
 *
 *  The routing framework allows us to define trees of routes. In our recipes
 *  example we could have defined our routes like this:
 *
 *     void initRoutes(Router router, RouteViewFactory view) {
 *        views.configure({
 *            'recipes': ngRoute(path: '/recipes', view: 'recipes.html'),
 *            'addRecipe': ngRoute(path: '/addRecipe', view: 'addRecipe.html'),
 *            'recipe': ngRoute(path: '/recipe/:recipeId', mount: {
 *                'view': ngRoute(path: '/view', view: 'viewRecipe.html'),
 *                'edit': ngRoute(path: '/edit', view: 'editRecipe.html),
 *            })
 *        });
 */
library angular.routing;

import 'dart:async';
import 'dart:html';

import 'package:di/di.dart';
import 'package:angular/application.dart';
import 'package:angular/core/annotation_src.dart';
import 'package:angular/core/module_internal.dart';
import 'package:angular/core_dom/module_internal.dart';
import 'package:route_hierarchical/client.dart';

part 'routing.dart';
part 'ng_view.dart';
part 'ng_bind_route.dart';

class RoutingModule extends Module {
  RoutingModule({bool usePushState: true}) {
    bind(NgRoutingUsePushState);
    bind(Router, toFactory: (injector) {
      var useFragment = !injector.get(NgRoutingUsePushState).usePushState;
      return new Router(useFragment: useFragment, windowImpl: injector.get(Window));
    });
    bind(NgRoutingHelper);
    bind(RouteProvider, toValue: null);
    bind(RouteInitializer, toValue: null);
    bind(RouteInitializerFn, toValue: null);

    // directives
    bind(NgView, toValue: null);
    bind(NgBindRoute);
  }
}

/**
 * Allows configuration of [Router.useFragment]. By default [usePushState] is
 * true, so the router will listen to [Window.onPopState] and route URLs like
 * "http://host:port/foo/bar?baz=qux". Both the path and query parts of the URL
 * are used by the router. If [usePushState] is false, router will listen to
 * [Window.onHashChange] and route URLs like
 * "http://host:port/path#/foo/bar?baz=qux". Everything after hash (#) is used
 * by the router.
 */
@Injectable()
class NgRoutingUsePushState {
  final bool usePushState;
  NgRoutingUsePushState(): usePushState = true;
  NgRoutingUsePushState.value(this.usePushState);
}
