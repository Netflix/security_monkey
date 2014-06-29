part of angular.animate;

/**
 * This defines the standard set of CSS animation classes, transitions, and
 * nomenclature that will eventually be the foundation of the AngularDart
 * animation framework. This implementation uses the [AnimationLoop] class to
 * queue and run CSS based transition and keyframe animations.
 */
@Injectable()
class CssAnimate implements Animate {
  static const NG_ANIMATE = "ng-animate";
  static const NG_MOVE = "ng-move";
  static const NG_INSERT = "ng-enter";
  static const NG_REMOVE = "ng-leave";

  static const NG_ADD_POSTFIX = "-add";
  static const NG_REMOVE_POSTFIX = "-remove";
  static const NG_ACTIVE_POSTFIX = "-active";

  final NoOpAnimation _noOp = new NoOpAnimation();

  final AnimationLoop _runner;
  final AnimationOptimizer _optimizer;
  final CssAnimationMap _animationMap;

  CssAnimate(this._runner, this._animationMap, this._optimizer);

  Animation addClass(dom.Element element, String cssClass) {
    if (!_optimizer.shouldAnimate(element)) {
      element.classes.add(cssClass);
      return _noOp;
    }

    cancelAnimation(element, "$cssClass$NG_REMOVE_POSTFIX");
    var event = "$cssClass$NG_ADD_POSTFIX";
    return animate(element, event, addAtEnd: cssClass);
  }

  Animation removeClass(dom.Element element, String cssClass) {
    if (!_optimizer.shouldAnimate(element)) {
      element.classes.remove(cssClass);
      return _noOp;
    }

    cancelAnimation(element, "$cssClass$NG_ADD_POSTFIX");

    var event = "$cssClass$NG_REMOVE_POSTFIX";
    return animate(element, event, removeAtEnd: cssClass);
  }

  Animation insert(Iterable<dom.Node> nodes, dom.Node parent,
                         { dom.Node insertBefore }) {
    util.domInsert(nodes, parent, insertBefore: insertBefore);

    var animations = util.getElements(nodes)
        .where((el) =>_optimizer.shouldAnimate(el))
        .map((el) => animate(el, NG_INSERT));

    return _animationFromList(animations);
  }

  Animation remove(Iterable<dom.Node> nodes) {
    var animations = nodes.map((node) {
      if (node.nodeType == dom.Node.ELEMENT_NODE &&
          _optimizer.shouldAnimate(node)) {
        return animate(node, NG_REMOVE);
      }
      return _noOp;
    });

    var result = _animationFromList(animations)..onCompleted.then((result) {
      if (result.isCompleted) nodes.toList().forEach((n) => n.remove());
    });

    return result;
  }

  Animation move(Iterable<dom.Node> nodes, dom.Node parent,
                       { dom.Node insertBefore }) {
    util.domMove(nodes, parent, insertBefore: insertBefore);

    var animations = util.getElements(nodes)
        .where((el) => _optimizer.shouldAnimate(el))
        .map((el) => animate(el, NG_MOVE));

    return _animationFromList(animations);
  }

  /**
   * Run a css animation on a element for a given css class. If the css
   * animation already exists, the method will attempt to return the existing
   * instance.
   */
  CssAnimation animate(
      dom.Element element,
      String event,
      { String addAtStart,
        String addAtEnd,
        String removeAtStart,
        String removeAtEnd }) {

    var _existing = _animationMap.findExisting(element, event);
    if (_existing != null) return _existing;

    var animation = new CssAnimation(
        element,
        event,
        "$event$NG_ACTIVE_POSTFIX",
        addAtStart: addAtStart,
        addAtEnd: addAtEnd,
        removeAtStart: removeAtStart,
        removeAtEnd: removeAtEnd,
        animationMap: _animationMap,
        optimizer: _optimizer);

    _runner.play(animation);
    return animation;
  }

  /**
   * For a given element and css event, attempt to find an existing instance
   * of the given animation and cancel it.
   */
  void cancelAnimation(dom.Element element, String event) {
    var existing = _animationMap.findExisting(element, event);

    if (existing != null) existing.cancel();
  }
}

/**
 * Tracked set of currently running css animations grouped by element.
 */
@Injectable()
class CssAnimationMap {
  final Map<dom.Element, Map<String, CssAnimation>> cssAnimations
      = new Map<dom.Element, Map<String, CssAnimation>>();

  void track(CssAnimation animation) {
    var animations = cssAnimations.putIfAbsent(animation.element,
        () => <String, CssAnimation>{});
    animations[animation.eventClass] = animation;
  }

  void forget(CssAnimation animation) {
    var animations = cssAnimations[animation.element];
    animations.remove(animation.eventClass);
    if (animations.length == 0) cssAnimations.remove(animation.element);
  }

  CssAnimation findExisting(dom.Element element, String event) {
    var animations = cssAnimations[element];
    if (animations == null) return null;
    return animations[event];
  }
}
