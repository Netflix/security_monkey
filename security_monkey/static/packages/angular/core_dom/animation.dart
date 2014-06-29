part of angular.core.dom_internal;

/**
 * The [Animate] service provides dom lifecycle management, detection and
 * analysis of css animations, and hooks for custom animations. When any of
 * these animations are run, [Animation]s are returned so the animation can be
 * controlled and so that custom dom manipulations can occur when animations
 * complete.
 */
@Injectable()
class Animate {
  /**
   * Add the [cssClass] to the classes on [element] after running any
   * defined animations.
   */
  Animation addClass(dom.Element element, String cssClass) {
    element.classes.add(cssClass);
    return new NoOpAnimation();
  }

  /**
    * Remove the [cssClass] from the classes on [element] after running any
    * defined animations.
    */
  Animation removeClass(dom.Element element, String cssClass) {
    element.classes.remove(cssClass);
    return new NoOpAnimation();
  }

  /**
   * Perform an 'enter' animation for each element in [nodes]. The elements
   * must exist in the dom. This is equivalent to running enter on each element
   * in [nodes] and returning Future.wait(handles); for the onCompleted
   * property on [Animation].
   */
  Animation insert(Iterable<dom.Node> nodes, dom.Node parent,
                         { dom.Node insertBefore }) {
    util.domInsert(nodes, parent, insertBefore: insertBefore);
    return new NoOpAnimation();
  }

  /**
   * Perform a 'remove' animation for each element in [nodes]. The elements
   * must exist in the dom and should not be detached until the [onCompleted]
   * future on the [Animation] is executed AND the [AnimationResult] is
   * [AnimationResult.COMPLETED] or [AnimationResult.COMPLETED_IGNORED].
   *
   * This is equivalent to running remove on each element in [nodes] and
   * returning Future.wait(handles); for the onCompleted property on
   * [Animation].
   */
  Animation remove(Iterable<dom.Node> nodes) {
    util.domRemove(nodes.toList(growable: false));
    return new NoOpAnimation();
  }

  /**
   * Perform a 'move' animation for each element in [nodes]. The elements
   * must exist in the dom. This is equivalent to running move on each element
   * in [nodes] and returning Future.wait(handles); for the onCompleted
   * property on [Animation].
   */
  Animation move(Iterable<dom.Node> nodes, dom.Node parent,
                       { dom.Node insertBefore }) {
    util.domMove(nodes, parent, insertBefore: insertBefore);
    return new NoOpAnimation();
  }
}


/**
 * Animation handle for controlling and listening to animation completion.
 */
abstract class Animation {
  /**
   * Executed once when the animation is completed with the type of completion
   * result.
   */
  async.Future<AnimationResult> get onCompleted;

  /**
   * Stop and complete the animation immediately. This has no effect if the
   * animation has already completed.
   *
   * The onCompleted future will be executed if the animation has not been
   * completed.
   */
  void complete();

  /**
   * Stop and cancel the animation immediately. This has no effect if the
   * animation has already completed.
   *
   * The onCompleted future will be executed if the animation has not been
   * completed.
   */
  void cancel();
}

/**
 * Completed animation handle that is used when an animation is ignored and the
 * final effect of the animation is immediately completed.
 *
 * TODO(codelogic): consider making a singleton instance. Depends on how future
 * behaves.
 */
class NoOpAnimation extends Animation {
  async.Future<AnimationResult> _future;
  get onCompleted {
    if (_future == null) {
      _future = new async.Future.value(AnimationResult.COMPLETED_IGNORED);
    }
    return _future;
  }

  complete() { }
  cancel() { }
}

/**
 * Final result of an animation after it is no longer attached to the element.
 */
class AnimationResult {
  /// Animation was run (if it exists) and completed successfully.
  static const COMPLETED = const AnimationResult._('COMPLETED');

  /// Animation was skipped, but should be continued.
  static const COMPLETED_IGNORED = const AnimationResult._('COMPLETED_IGNORED');

  /// A [CANCELED] animation should not proceed with it's final effects.
  static const CANCELED = const AnimationResult._('CANCELED');

  /// Convenience method if you don't care exactly how an animation completed
  /// only that it did.
  bool get isCompleted => this == COMPLETED || this == COMPLETED_IGNORED;

  final String value;
  const AnimationResult._(this.value);
}
