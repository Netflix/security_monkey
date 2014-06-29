part of angular.directive;

/**
 * Hides elements on the page while the application loads. `Selector: [ng-cloak], .ng-cloak`
 *
 * This prevents template artifacts from being briefly displayed by the browser in their raw (uncompiled) form while
 * your application is loading. Use this directive to avoid the undesirable flicker effect caused by the HTML template
 * display.
 *
 * The directive can be applied to the `<body>` element, but typically a fine-grained application is preferred in order
 * to benefit from progressive rendering of the browser view.
 *
 * `ng-cloak` works in conjunction with a css rule:
 *
 *     [ng-cloak], [data-ng-cloak], .ng-cloak {
 *        display: none !important;
 *     }
 *
 * When this css rule is loaded by the browser, all elements (including their children) that are tagged with `ng-cloak`
 * are hidden. When Angular encounters this directive during the compilation of the template, it deletes the `ng-cloak`
 * element attribute, making the compiled element visible.
 *
 * # Examples
 * NgCloak can be used as an attribute:
 *
 *     <div ng-cloak>
 *
 * Or as a class name:
 *
 *      <div class="myclass ng-cloak">
 *
 */
@Decorator(selector: '[ng-cloak]')
@Decorator(selector: '.ng-cloak')
class NgCloak {
  NgCloak(dom.Element element, Animate animate) {
    element.attributes.remove('ng-cloak');
    animate.removeClass(element, 'ng-cloak');
  }
}
