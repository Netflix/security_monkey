/**
 * CSS animation and DOM lifecycle management for AngularDart apps.
 *
 * The [angular.animate](#angular/angular-animate) library makes it easier to build animations
 * that affect the lifecycle of DOM elements. A useful example of this is animating the
 * removal of an element from the DOM. In order to do this ideally the
 * operation should immediatly execute and manipulate the data model,
 * and the framework should handle the actual remove of the DOM element once
 * the animation complets. This ensures that the logic and model of the
 * application is seperated so that the state of the model can be reasoned
 * about without having to wory about future modifications of the model.
 * This library uses computed css styles to calculate the total duration
 * of an animation and handles the addition, removal, and modification of DOM
 * elements for block level directives such as `ng-if`, `ng-repeat`,
 * `ng-hide`, and more.
 *
 * To use, install the AnimationModule into your main module:
 *
 *     var module = new Module()
 *       ..install(new AnimationModule());
 *
 * Once the module has been installed, all block level DOM manipulations will
 * be routed through the [CssAnimate] class instead of the
 * default [NgAnimate] implementation. This will, in turn,
 * perform the tracking, manipulation, and computation for animations.
 *
 * As an example of how this works, let's walk through what happens whan an
 * element is added to the DOM. The [CssAnimate] implementation will add the
 * `.ng-enter` class to new DOM elements when they are inserted into the DOM
 * by a directive and will read the computed style. If there is a
 * transition or keyframe animation, that animation duration will be read,
 * and the animation will be performed. The `.ng-enter-active` class will be
 * added to the DOM element to set the target state for transition based
 * animations. When the animation is complete (determined by the
 * precomputed duration) the `.ng-enter` and `.ng-enter-active` classes
 * will be removed from the DOM element.
 *
 * When removing elements from the DOM, a simliar pattern is followed. The
 * `.ng-leave` class will be added to an element, the transition and / or
 * keyframe animation duration will be computed, and if it is non-zero the
 * animation will be run by adding the `.ng-leave-active` class. When
 * the animation completes, the element will be physically removed from the
 * DOM.
 *
 * The same set of steps is run for each of the following types of DOM
 * manipulation:
 *
 * * `.ng-enter`
 * * `.ng-leave`
 * * `.ng-move`
 * * `.{cssclass}-add`
 * * `.{cssclass}-remove`
 *
 * When writing the css for animating a component you should avoid putting
 * css transitions on elements that might be animated or there may be
 * unintended pauses or side effects when an element is removed.
 *
 * Fade out example:
 *
 * HTML:
 *     <div class="goodbye" ng-if="ctrl.visible">
 *       Goodbye world!
 *     </div>
 *
 * CSS:
 *     .goodbye.ng-leave {
 *       opacity: 1;
 *       transition: opacity 1s;
 *     }
 *     .goodbye.ng-leave.ng-leave-active {
 *       opacity: 0;
 *     }
 *
 * This will perform a fade out animation on the 'goodby' div when the
 * `ctrl.visible` property goes from `true` to `false`.
 *
 * The [CssAnimate] will also do optimizations on running animations by
 * preventing child DOM animations with the [AnimationOptimizer]. This
 * prevents transitions on child elements while the parent is animating,
 * but will not stop running transitions once they have started.
 *
 * Finally, it's possible to change the behavior of the [AnimationOptimizer]
 * by using the `ng-animate` and `ng-animate-children` with the options
 * `never`, `always`, or `auto`. `ng-animate` works only on the specific
 * element it is applied too and will override other optimizations if `never`
 * or `always` is specified. `ng-animate` defaults to `auto` which will
 * defer to the `ng-animate-children` on a parent element or the currently
 * running animation check.
 *
 * `ng-animate-children` allows animation to be controlled on large chunks of
 * DOM. It only affects child elements, and allows the `always`, `never`,
 * and `auto` values to be specified. Always will always attempt animations
 * on child DOM directives, never will always prevent them (except in the
 * case where a given element has `ng-animate="always"` specified),
 * and `auto` will defer the decision to the currently running animation
 * check.
 */

library angular.animate;

import 'dart:async';
import 'dart:html' as dom;

import 'package:angular/core/annotation.dart';
import 'package:angular/core/module_internal.dart';
import 'package:angular/core_dom/module_internal.dart';
import 'package:angular/core_dom/dom_util.dart' as util;
import 'package:logging/logging.dart';
import 'package:perf_api/perf_api.dart';
import 'package:di/di.dart';

@MirrorsUsed(targets: const [
    'angular.animate'
])
import 'dart:mirrors' show MirrorsUsed;

part 'animations.dart';
part 'animation_loop.dart';
part 'animation_optimizer.dart';
part 'css_animate.dart';
part 'css_animation.dart';
part 'ng_animate.dart';

final Logger _logger = new Logger('ng.animate');

/**
 * Installing the AnimationModule will install a [CssAnimate] implementation of
 * the [NgAnimate] interface in your application. This will change the behavior
 * of view construction, and some of the native directives to allow you to add
 * and define css transition and keyframe animations for the styles of your
 * elements.
 * 
 *   Example html:
 *
 *     <div ng-if="ctrl.myBoolean" class="my-div">...</div>
 *   
 *   Example css defining an opacity transition over .5 seconds using the
 *   `.ng-enter` and `.ng-leave` css classes:
 *
 *     .my-div.ng-enter {
 *       transition: all 500ms;
 *       opacity: 0;
 *     }
 *     .my-div.ng-enter-active {
 *       opacity: 1;
 *     }
 *     
 *     .my-div.ng-leave {
 *       transition: all 500ms;
 *       opacity: 1;
 *     }
 *     .my-div.ng-leave-active {
 *       opacity: 0;
 *     }
 */
class AnimationModule extends Module {
  AnimationModule() {
    bind(AnimationFrame);
    bind(AnimationLoop);
    bind(CssAnimationMap);
    bind(AnimationOptimizer);
    bind(NgAnimate, toValue: null);
    bind(NgAnimateChildren);
    bind(Animate, toImplementation: CssAnimate);
  }
}
