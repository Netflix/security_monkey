part of angular.animate;

/**
 * Window.animationFrame update loop that tracks and drives
 * [LoopedAnimations]'s.
 */
@Injectable()
class AnimationLoop {
  final AnimationFrame _frames;
  final Profiler _profiler;
  final List<LoopedAnimation> _animations = [];
  final VmTurnZone _zone;

  bool _animationFrameQueued = false;

  /**
   * The animation runner requires an [AnimationFrame] to drive the animation
   * frames, and profiler will report timing information for each of the
   * animation frames.
   */
  AnimationLoop(this._frames, this._profiler, this._zone);

  /**
   * Start and play an animation through the state transitions defined in
   * [Animation].
   */
  void play(LoopedAnimation animation) {
    _animations.add(animation);
    _queueAnimationFrame();
  }

  void _queueAnimationFrame() {
    if (!_animationFrameQueued) {
      _animationFrameQueued = true;

      // TODO(codleogic): This should run outside of an angular scope digest.
      _zone.runOutsideAngular(() {
        _frames.animationFrame.then((timeInMs) => _animationFrame(timeInMs))
            .catchError((error) => print(error));
      });
    }
  }

  /* On the browsers animation frame event, update each of the tracked
   * animations. Group dom reads first, and and writes second.
   *
   *  At any point any animation may be updated by calling interrupt and cancel
   *  with a reference to the [Animation] to cancel. The [AnimationRunner] will
   *  then forget about the [Animation] and will not call any further methods on
   *  the [Animation].
   */
  void _animationFrame(num timeInMs) {
    _profiler.startTimer("AnimationRunner.AnimationFrame");
    _animationFrameQueued = false;

    _profiler.startTimer("AnimationRunner.AnimationFrame.DomReads");
    // Dom reads
    _read(timeInMs);
    _profiler.stopTimer("AnimationRunner.AnimationFrame.DomReads");

    _profiler.startTimer("AnimationRunner.AnimationFrame.DomMutates");
    // Dom mutates
    _update(timeInMs);
    _profiler.stopTimer("AnimationRunner.AnimationFrame.DomMutates");

    // We don't need to continue queuing animation frames
    // if there are no more animations to process.
    if (_animations.length > 0) {
      _queueAnimationFrame();
    }

    _profiler.stopTimer("AnimationRunner.AnimationFrame");
  }

  void _update(num timeInMs) {
    for (int i=0; i< _animations.length; i++) {
      var controller = _animations[i];
      if (!controller.update(timeInMs)) {
        _animations.removeAt(i--);
      }
    }
  }

  void _read(num timeInMs) {
    for (int i=0; i< _animations.length; i++) {
      var animation = _animations[i];
      animation.read(timeInMs);
    }
  }

  /**
   * Stop tracking and updating the [animation].
   */
  void forget(LoopedAnimation animation) {
    assert(animation != null);
    _animations.remove(animation);
  }
}

/**
 * Wrapper around window.requestAnimationFrame so it can be intercepted and
 * tested.
 */
@Injectable()
class AnimationFrame {
  final dom.Window _wnd;
  Future<num> get animationFrame => _wnd.animationFrame;

  AnimationFrame(this._wnd);
}
