part of angular.core_internal;

/**
 * Handles a [VmTurnZone] onTurnDone event.
 */
typedef void ZoneOnTurnDone();

/**
 * Handles a [VmTurnZone] onTurnDone event.
 */
typedef void ZoneOnTurnStart();

typedef void ZoneScheduleMicrotask(fn());

/**
 * Handles a [VmTurnZone] onError event.
 */
typedef void ZoneOnError(dynamic error, dynamic stacktrace,
                         LongStackTrace longStacktrace);

/**
 * Contains the locations of async calls across VM turns.
 */
class LongStackTrace {
  final String reason;
  final dynamic stacktrace;
  final LongStackTrace parent;

  LongStackTrace(this.reason, this.stacktrace, this.parent);

  toString() {
    List<String> frames = '${this.stacktrace}'.split('\n')
        .where((frame) =>
            frame.indexOf('(dart:') == -1 && // skip dart runtime libs
            frame.indexOf('(package:angular/zone.dart') == -1 // skip angular zone
        ).toList()..insert(0, reason);
    var parent = this.parent == null ? '' : this.parent;
    return '${frames.join("\n    ")}\n$parent';
  }
}

/**
 * A [Zone] wrapper that lets you schedule tasks after its private microtask
 * queue is exhausted but before the next "turn", i.e. event loop iteration.
 * This lets you freely schedule microtasks that prepare data, and set an
 * [onTurnDone] handler that will consume that data after it's ready but before
 * the browser has a chance to re-render.
 * The wrapper maintains an "inner" and "outer" [Zone] and a private queue of
 * all the microtasks scheduled on the inner [Zone].
 *
 * In a typical app, [ngDynamicApp] or [ngStaticApp] will create a singleton
 * [VmTurnZone] whose outer [Zone] is the root [Zone] and whose default [onTurnDone]
 * runs the Angular digest.  A component may want to inject this singleton if it
 * needs to run code _outside_ the Angular digest.
 */
class VmTurnZone {
  /// an "outer" [Zone], which is the one that created this.
  async.Zone _outerZone;

  /// an "inner" [Zone], which is a child of the outer [Zone].
  async.Zone _innerZone;

  /**
   * Associates with this
   *
   * - an "outer" [Zone], which is the one that created this.
   * - an "inner" [Zone], which is a child of the outer [Zone].
   *
   * Defaults [onError] to forward errors to the outer [Zone].
   * Defaults [onTurnStart] and [onTurnDone] to no-op functions.
   */
  VmTurnZone() {
    _outerZone = async.Zone.current;
    _innerZone = _outerZone.fork(specification: new async.ZoneSpecification(
        run: _onRun,
        runUnary: _onRunUnary,
        scheduleMicrotask: _onScheduleMicrotask,
        handleUncaughtError: _uncaughtError
    ));
    onError = _defaultOnError;
    onTurnDone = _defaultOnTurnDone;
    onTurnStart = _defaultOnTurnStart;
    onScheduleMicrotask = _defaultOnScheduleMicrotask;
  }

  List _asyncQueue = [];
  bool _errorThrownFromOnRun = false;

  var _currentlyInTurn = false;
  _onRunBase(async.Zone self, async.ZoneDelegate delegate, async.Zone zone, fn()) {
    _runningInTurn++;
    try {
      if (!_currentlyInTurn) {
        _currentlyInTurn = true;
        delegate.run(zone, onTurnStart);
      }
      return fn();
    } catch (e, s) {
      onError(e, s, _longStacktrace);
      _errorThrownFromOnRun = true;
      rethrow;
    } finally {
      _runningInTurn--;
      if (_runningInTurn == 0) _finishTurn(zone, delegate);
    }
  }
  // Called from the parent zone.
  _onRun(async.Zone self, async.ZoneDelegate delegate, async.Zone zone, fn()) =>
      _onRunBase(self, delegate, zone, () => delegate.run(zone, fn));

  _onRunUnary(async.Zone self, async.ZoneDelegate delegate, async.Zone zone,
              fn(args), args) =>
      _onRunBase(self, delegate, zone, () => delegate.runUnary(zone, fn, args));

  _onScheduleMicrotask(async.Zone self, async.ZoneDelegate delegate,
                       async.Zone zone, fn()) {
    onScheduleMicrotask(() => delegate.run(zone, fn));
    if (_runningInTurn == 0 && !_inFinishTurn)  _finishTurn(zone, delegate);
  }

  _uncaughtError(async.Zone self, async.ZoneDelegate delegate, async.Zone zone,
                 e, StackTrace s) {
    if (!_errorThrownFromOnRun) onError(e, s, _longStacktrace);
    _errorThrownFromOnRun = false;
  }

  var _inFinishTurn = false;
  _finishTurn(zone, delegate) {
    if (_inFinishTurn) return;
    _inFinishTurn = true;
    try {
      // Two loops here: the inner one runs all queued microtasks,
      // the outer runs onTurnDone (e.g. scope.digest) and then
      // any microtasks which may have been queued from onTurnDone.
      // If any microtasks were scheduled during onTurnDone, onTurnStart
      // will be executed before those microtasks.
      do {
        if (!_currentlyInTurn) {
          _currentlyInTurn = true;
          delegate.run(zone, onTurnStart);
        }
        while (!_asyncQueue.isEmpty) {
          _asyncQueue.removeAt(0)();
        }
        delegate.run(zone, onTurnDone);
        _currentlyInTurn = false;
      } while (!_asyncQueue.isEmpty);
    } catch (e, s) {
      onError(e, s, _longStacktrace);
      _errorThrownFromOnRun = true;
      rethrow;
    } finally {
      _inFinishTurn = false;
    }
  }

  int _runningInTurn = 0;

  /**
   * Called with any errors from the inner zone.
   */
  ZoneOnError onError;
  /// Forwards uncaught exceptions to the outer zone.
  void _defaultOnError(dynamic e, dynamic s, LongStackTrace ls) =>
      _outerZone.handleUncaughtError(e, s);

  /**
   * Called at the beginning of each VM turn in which inner zone code runs.
   * "At the beginning" means before any of the microtasks from the private
   * microtask queue of the inner zone is executed. Notes
   *
   * - [onTurnStart] runs repeatedly until no more microstasks are scheduled
   *   within [onTurnStart], [run] or [onTurnDone]. You usually don't want it to
   *   schedule any.  For example, if its first line of code is `new Future.value()`,
   *   the turn will _never_ end.
   */
  ZoneOnTurnStart onTurnStart;
  void _defaultOnTurnStart() => null;

  /**
   * Called at the end of each VM turn in which inner zone code runs.
   * "At the end" means after the private microtask queue of the inner zone is
   * exhausted but before the next VM turn.  Notes
   *
   * - This won't wait for microtasks scheduled in zones other than the inner
   *   zone, e.g. those scheduled with [runOutsideAngular].
   * - [onTurnDone] runs repeatedly until no more tasks are scheduled within
   *   [onTurnStart], [run] or [onTurnDone]. You usually don't want it to
   *   schedule any.  For example, if its first line of code is `new Future.value()`,
   *   the turn will _never_ end.
   */
  ZoneOnTurnDone onTurnDone;
  void _defaultOnTurnDone() => null;

  /**
   * Called any time a microtask is scheduled. If you override [onScheduleMicrotask], you
   * are expected to call the function at some point.
   */
  ZoneScheduleMicrotask onScheduleMicrotask;
  void _defaultOnScheduleMicrotask(fn) => _asyncQueue.add(fn);

  LongStackTrace _longStacktrace = null;

  LongStackTrace _getLongStacktrace(name) {
    var shortStacktrace = 'Long-stacktraces supressed in production.';
    assert((shortStacktrace = _getStacktrace()) != null);
    return new LongStackTrace(name, shortStacktrace, _longStacktrace);
  }

  StackTrace _getStacktrace() {
    try {
      throw [];
    } catch (e, s) {
      return s;
    }
  }

  /**
   * Runs [body] in the inner zone and returns whatever it returns.
   */
  dynamic run(body()) => _innerZone.run(body);

  /**
   * Runs [body] in the outer zone and returns whatever it returns.
   * In a typical app where the inner zone is the Angular zone, this allows
   * one to escape Angular's auto-digest mechanism.
   *
   *     myFunction(VmTurnZone zone, Element element) {
   *       element.onClick.listen(() {
   *         // auto-digest will run after element click.
   *       });
   *       zone.runOutsideAngular(() {
   *         element.onMouseMove.listen(() {
   *           // auto-digest will NOT run after mouse move
   *         });
   *       });
   *     }
   */
  dynamic runOutsideAngular(body()) => _outerZone.run(body);

  /**
   * Throws an [AssertionError] if no task is currently running in the inner
   * zone.  In a typical app where the inner zone is the Angular zone, this can
   * be used to assert that the digest will indeed run at the end of the current
   * turn.
   */
  void assertInTurn() {
    assert(_runningInTurn > 0 || _inFinishTurn);
  }

  /**
   * Same as [assertInTurn].
   */
  void assertInZone() {
    assertInTurn();
  }
}
