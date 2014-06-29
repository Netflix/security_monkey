part of angular.animate;

/**
 * The optimizer tracks elements and running animations. It's used to control
 * and optionally skip certain animations that are deemed "expensive" such as
 * running animations on child elements while the dom parent is also running an
 * animation.
 */
@Injectable()
class AnimationOptimizer {
  final Map<dom.Element, Set<Animation>> _elements = new Map<dom.Element,
      Set<Animation>>();
  final Map<Animation, dom.Element> _animations = new Map<Animation,
      dom.Element>();

  final Map<dom.Node, bool> _alwaysAnimate = new Map<dom.Node, bool>();
  final Map<dom.Node, bool> _alwaysAnimateChildren = new Map<dom.Node, bool>();

  Expando _expando;

  AnimationOptimizer(this._expando);

  /**
   * Track an animation that is running against a dom element. Usually, this
   * should occur when an animation starts.
   */
  void track(Animation animation, dom.Element forElement) {
    if (forElement != null) {
      var animations = _elements.putIfAbsent(forElement, () =>
          new Set<Animation>());
      animations.add(animation);
      _animations[animation] = forElement;
    }
  }

  /**
   * Stop tracking an animation. If it's the last tracked animation on an
   * element forget about that element as well.
   */
  void forget(Animation animation) {
    var element = _animations.remove(animation);
    if (element != null) {
      var animationsOnElement = _elements[element];
      animationsOnElement.remove(animation);
      // It may be more efficient just to keep sets around even after
      // animations complete.
      if (animationsOnElement.length == 0) {
        _elements.remove(element);
      }
    }
  }

  /**
   * Since we can't overload forget...
   */
  void detachAlwaysAnimateOptions(dom.Element element) {
    _alwaysAnimate.remove(element);
    _alwaysAnimateChildren.remove(element);
  }

  /**
   * Control animation for a specific element, ignoring every other option.
   *   [mode] "always" will always animate this element.
   *   [mode] "never" will never animate this element.
   *   [mode] "auto" will detect if a parent animation is running or has child animations set.
   */
  void alwaysAnimate(dom.Element element, String mode) {
    if (mode == "always") {
      _alwaysAnimate[element] = true;
    } else if (mode == "never") {
      _alwaysAnimate[element] = false;
    } else if (mode == "auto") {
      _alwaysAnimate.remove(element);
    }
  }

  /**
   * Control animation for child elements, ignoring running animations unless 'auto' is provided as an option.
   *   [mode] "always" will always animate children, unless it is specifically marked not to by [alwaysAnimate].
   *   [mode] "never" will never animate children.
   *   [mode] "auto" will detect if a parent animation is running or has child animations set.
   */
  void alwaysAnimateChildren(dom.Element element, String mode) {
    if (mode == "always") {
      _alwaysAnimateChildren[element] = true;
    } else if (mode == "never") {
      _alwaysAnimateChildren[element] = false;
    } else if (mode == "auto") {
      _alwaysAnimateChildren.remove(element);
    }
  }

  /**
   * Returns true if there is tracked animation on the given element.
   */
  bool _isAnimating(dom.Element element) {
    return _elements.containsKey(element);
  }

  /**
   * Given all the information this optimizer knows about currently executing
   * animations, return [true] if this element can be animated in an ideal case
   * and [false] if the optimizer thinks that it should not execute.
   */
  bool shouldAnimate(dom.Node node) {
    bool alwaysAnimate = _alwaysAnimate[node];
    if (alwaysAnimate != null) {
      return alwaysAnimate;
    }

    // If there are 'always allow' or 'always prevent' animations declared,
    // fallback to the automatic detection of running parent animations. By
    // default, we assume that we can run.
    bool autoDecision = true;

    node = node.parentNode;
    while (node != null) {
      // Does this node give us animation information about our children?
      alwaysAnimate = _alwaysAnimateChildren[node];
      if (alwaysAnimate != null) {
        return alwaysAnimate;
      }

      // If we hit a running parent animation, we still need to continue up
      // the dom tree to see if there is or is not an 'alwaysAnimateChildren'
      // decision somewhere.
      if (autoDecision
          && node.nodeType == dom.Node.ELEMENT_NODE
          && _isAnimating(node)) {
        // If there is an already running animation, don't animate.
        autoDecision = false;
      }

      // If we hit a null parent, try to break out of shadow dom.
      if (node.parentNode == null) {
        var probe = _findElementProbe(node);
        if (probe != null && probe.parent != null) {
          // Escape shadow dom!
          node = probe.parent.element;
        } else {
          // If we can't go any further, return the auto decision because we
          // havent hit any other more important optimizations.
          return autoDecision;
        }
      } else {
        node = node.parentNode;
      }
    }

    return autoDecision;
  }

  // Search and find the element probe for a given node.
  ElementProbe _findElementProbe(dom.Node node) {
    while (node != null) {
      if (_expando[node] != null) {
        return _expando[node];
      }
      node = node.parentNode;
    }
    return null;
  }
}
