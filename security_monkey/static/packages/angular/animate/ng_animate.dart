part of angular.animate;

/**
 * This provides DOM controls for turning animations on and off for individual
 * dom elements. Valid options are [always] [never] and [auto]. If this
 * directive is not applied the default value is [auto] for animation.
 */
@Decorator(selector: '[ng-animate]',
    map: const {'ng-animate': '@option'})
class NgAnimate  extends AbstractNgAnimate {
  set option(value) {
    _option = value;
    _optimizer.alwaysAnimate(_element, _option);
  }

  NgAnimate(dom.Element element, AnimationOptimizer optimizer)
      : super(element, optimizer);
}

/**
 * This provides DOM controls for turning animations on and off for child
 * dom elements. Valid options are [always] [never] and [auto]. If this
 * directive is not applied the default value is [auto] for animation.
 *
 * Values provided in [ng-animate] will override this directive since they are
 * more specific.
 */
@Decorator(selector: '[ng-animate-children]',
    map: const {'ng-animate-children': '@option'})
class NgAnimateChildren extends AbstractNgAnimate {
  set option(value) {
    _option = value;
    _optimizer.alwaysAnimateChildren(_element, _option);
  }

  NgAnimateChildren(dom.Element element, AnimationOptimizer optimizer)
    : super(element, optimizer);
}

/**
 * Base class for directives that control animations with an
 * [AnimationOptimizer].
 */
abstract class AbstractNgAnimate implements DetachAware {
  final AnimationOptimizer _optimizer;
  final dom.Element _element;

  String _option = "auto";
  String get option => _option;
  set option(value);

  AbstractNgAnimate(this._element, this._optimizer);

  detach() {
    _optimizer.detachAlwaysAnimateOptions(_element);
  }
}
