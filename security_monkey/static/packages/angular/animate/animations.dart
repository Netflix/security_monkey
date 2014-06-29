part of angular.animate;

/**
 * A [LoopedAnimation] is used with the [AnimationLoop] to drive window
 * animation frame animations. This provides hooks for dom reads and updates so
 * that they can be batched together to prevent excessive dom recalculations
 * when running multiple animations.
 */
abstract class LoopedAnimation implements Animation {

  /**
   * This is used to batch dom read operations to prevent excessive
   * recalculations when dom is modified.
   *
   * [timeInMs] is the time since the last animation frame.
   */
  void read(num timeInMs) { }
  
  /**
   * Occurs every animation frame. Return false to stop receiving animation
   * frame updates. Detach will be called after [update] returns false.
   *
   * [timeInMs] is the time since the last animation frame.
   */
  bool update(num timeInMs) { return false; }
}

/**
 * This is a proxy class for dealing with a set of elements where the 'same'
 * or similar animations are being run on them and it's more convenient to have
 * a merged animation to control and listen to a set of animations.
 */
class AnimationList extends Animation {
  final List<Animation> _animations;
  Future<AnimationResult> _onCompleted;

  /**
   * [OnCompleted] executes once all the OnCompleted futures for each of the
   * animations completes.
   *
   * if every animation returns [AnimationResult.COMPLETED],
   *   [AnimationResult.COMPLETED] will be returned.
   * if any animation was [AnimationResult.COMPLETED_IGNORED] instead, even if
   *   some animations were completed, [AnimationResult.COMPLETED_IGNORED] will
   *   be returned.
   * if any animation was [AnimationResult.CANCELED], the result will be
   *   [AnimationResult.CANCELED].
   */
  Future<AnimationResult> get onCompleted {
    if (_onCompleted == null) {
      _onCompleted = Future.wait(_animations.map((x) => x.onCompleted))
        .then((results) {
          var rtrn = AnimationResult.COMPLETED;
          for (var result in results) {
            if (result == AnimationResult.CANCELED)
              return AnimationResult.CANCELED;
            if (result == AnimationResult.COMPLETED_IGNORED)
              rtrn = result;
          }
          return rtrn;
        });
    }
    
    return _onCompleted;
  }

  /// track and create a new [Animation] that acts as a proxy to a list of
  /// existing [Animation]s.
  AnimationList(this._animations);

  /// For each of the tracked [Animation]s, call complete().
  void complete() {
    for (var animation in _animations) {
      animation.complete();
    }
  }

  /// For each of the tracked [Animation]s, call cancel().
  void cancel() {
    for (var animation in _animations) {
      animation.cancel();
    }
  }
}

Animation _animationFromList(Iterable<Animation> animations) {
  if (animations == null) {
    return new NoOpAnimation();
  }

  List<Animation> list = animations.toList();
 
  if (list.length == 0) {
    return new NoOpAnimation();
  }
  if (list.length == 1) {
    return list.first;
  }
  return new AnimationList(list);
}
