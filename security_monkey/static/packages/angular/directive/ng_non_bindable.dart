part of angular.directive;

/**
 * Causes the compiler to ignore all Angular directives and markup on descendant
 * nodes of the matching element.  Note, however, that other directives and
 * markup on the element are still processed and that only descending the DOM
 * for compilation is prevented.
 *
 * Example:
 *
 *     <div foo="{{a}}" ng-non-bindable>
 *       <span ng-bind="b"></span>{{b}}
 *     </div>
 *
 * In the above example, because the `div` element has the `ng-non-bindable`
 * attribute set on it, the `ng-bind` directive and the interpolation for
 * `{{b}}` are not processed because Angular will not process the `span` child
 * element.  However, the `foo` attribute *will* be interpolated because it is
 * not on a child node.
 */
@Decorator(
    selector: '[ng-non-bindable]',
    children: Directive.IGNORE_CHILDREN)
class NgNonBindable {}
