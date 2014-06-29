part of angular.animate;

/**
 * [Animation] implementation for handling the standard angular 'event' and
 * 'event-active' class pattern with css. This will compute transition and
 * animation duration from the css classes and use it to complete futures when
 * the css animations complete.
 */
class CssAnimation extends LoopedAnimation {
  final CssAnimationMap _animationMap;
  final AnimationOptimizer _optimizer;

  final dom.Element element;
  final String addAtStart;
  final String addAtEnd;
  final String removeAtStart;
  final String removeAtEnd;

  final String eventClass;
  final String activeClass;

  final _completer = new Completer<AnimationResult>.sync();

  static const EXTRA_DURATION = 16.0; // Just a little extra time

  bool _active = true;
  bool _started = false;
  bool _isDisplayNone = false;

  Future<AnimationResult> get onCompleted => _completer.future;

  num _startTime;
  num _duration;

  CssAnimation(
      this.element,
      this.eventClass,
      this.activeClass,
      { this.addAtStart,
        this.removeAtStart,
        this.addAtEnd,
        this.removeAtEnd,
        CssAnimationMap animationMap,
        AnimationOptimizer optimizer })
      : _animationMap = animationMap,
        _optimizer = optimizer
  {
    if (_optimizer != null) _optimizer.track(this, element);
    if (_animationMap != null) _animationMap.track(this);
    element.classes.add(eventClass);
    if (addAtStart != null) element.classes.add(addAtStart);
    if (removeAtStart != null) element.classes.remove(removeAtStart);
  }

  void read(num timeInMs) {
    if (_active && _startTime == null) {
      _startTime = timeInMs;
      var style = element.getComputedStyle();
      _isDisplayNone = style.display == "none";
      _duration = util.computeLongestTransition(style);
      if (_duration > 0.0) {
        // Add a little extra time just to make sure transitions
        // fully complete and that we don't remove the animation classes
        // before it's completed.
        _duration = _duration + EXTRA_DURATION;
      }
    }
  }

  bool update(num timeInMs) {
    if (!_active) return false;

    if (timeInMs >= _startTime + _duration) {
      _complete(AnimationResult.COMPLETED);

      // TODO(codelogic): If the initial frame takes a significant amount of
      //   time, the computed duration + startTime might not actually represent
      //   the end of the animation
      // Done with the animation
      return false;
    } else if (!_started) {
      // This will always run after the first animationFrame is queued so that
      // inserted elements have the base event class applied before adding the
      // active class to the element. If this is not done, inserted dom nodes
      // will not run their enter animation.

      if (_isDisplayNone && removeAtEnd != null) {
        element.classes.remove(removeAtEnd);
      }

      element.classes.add(activeClass);
      _started = true;
    }

    // Continue updating
    return true;
  }

  void cancel() {
    if (_active) {
      _detach();
      if (addAtStart != null) element.classes.remove(addAtStart);
      if (removeAtStart != null) element.classes.add(removeAtStart);
      if (_completer != null) _completer.complete(AnimationResult.CANCELED);
    }
  }

  void complete() {
    _complete(AnimationResult.COMPLETED_IGNORED);
  }

  // Since there are two different ways to 'complete' an animation, this lets us
  // configure the final result.
  void _complete(AnimationResult result) {
    if (_active) {
      _detach();
      if (addAtEnd != null) element.classes.add(addAtEnd);
      if (removeAtEnd != null) element.classes.remove(removeAtEnd);
      _completer.complete(result);
    }
  }

  // Cleanup css event classes.
  void _detach() {
    _active = false;

    if (_animationMap != null) _animationMap.forget(this);
    if (_optimizer != null) _optimizer.forget(this);

    element.classes..remove(eventClass)..remove(activeClass);
  }
}
