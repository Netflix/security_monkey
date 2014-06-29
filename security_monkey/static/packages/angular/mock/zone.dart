library angular.mock_zone;

import 'dart:async' as dart_async;

// async and sync are function compositions.
class FunctionComposition {
  Function outer;
  Function inner;

  FunctionComposition(this.outer, this.inner);

  call() => outer(inner)();
}

final _asyncQueue = <Function>[];
final _timerQueue = <_TimerSpec>[];
final _asyncErrors = [];
bool _noMoreAsync = false;

/**
 * Processes the asynchronous queue established by [async].
 *
 * [microLeap] will process all items in the asynchronous queue,
 * including new items queued during its execution. It will re-raise
 * any exceptions that occur.
 *
 * NOTE: [microLeap] can only be used in [async] tests.
 *
 * Example:
 *
 *     it('should run async code', async(() {
 *       var thenRan = false;
 *       new Future.value('s').then((_) { thenRan = true; });
 *       expect(thenRan).toBe(false);
 *       microLeap();
 *       expect(thenRan).toBe(true);
 *     }));
 *
 *     it('should run chained thens', async(() {
 *       var log = [];
 *       new Future.value('s')
 *         .then((_) { log.add('firstThen'); })
 *         .then((_) { log.add('2ndThen'); });
 *       expect(log.join(' ')).toEqual('');
 *       microLeap();
 *       expect(log.join(' ')).toEqual('firstThen 2ndThen');
 *     }));
 *
 */
microLeap() {
  while (_asyncQueue.isNotEmpty) {
    // copy the queue as it may change.
    var toRun = new List.from(_asyncQueue);
    _asyncQueue.clear();
    // TODO: Support the case where multiple exceptions are thrown.
    // e.g. with a throwNextException() method.
    assert(_asyncErrors.isEmpty);
    toRun.forEach((fn) => fn());
    if (_asyncErrors.isNotEmpty) {
      var e = _asyncErrors.removeAt(0);
      throw ['Async error', e[0], e[1]];
    }
  }
}

/**
 * Returns whether the async queue is empty.
 */
isAsyncQueueEmpty() => _asyncQueue.isEmpty;

/**
 * Simulates a clock tick by running any scheduled timers. Can only be used
 * in [async] tests.Clock tick will call [microLeap] to process the microtask
 * queue before each timer callback.
 *
 * Note: microtasks scheduled form the last timer are not going to be processed.
 *
 * Example:
 *
 *     it('should run queued timer after sufficient clock ticks', async(() {
 *       bool timerRan = false;
 *       new Timer(new Duration(milliseconds: 10), () => timerRan = true);
 *
 *       clockTick(milliseconds: 9);
 *       expect(timerRan).toBeFalsy();
 *       clockTick(milliseconds: 1);
 *       expect(timerRan).toBeTruthy();
 *     }));
 *
 *     it('should run periodic timer', async(() {
 *       int timerRan = 0;
 *       new Timer.periodic(new Duration(milliseconds: 10), (_) => timerRan++);
 *
 *       clockTick(milliseconds: 9);
 *       expect(timerRan).toBe(0);
 *       clockTick(milliseconds: 1);
 *       expect(timerRan).toBe(1);
 *       clockTick(milliseconds: 30);
 *       expect(timerRan).toBe(4);
 *     }));
 */
void clockTick({int days: 0,
          int hours: 0,
          int minutes: 0,
          int seconds: 0,
          int milliseconds: 0,
          int microseconds: 0}) {
  var tickDuration = new Duration(days: days, hours: hours, minutes: minutes,
      seconds: seconds, milliseconds: milliseconds, microseconds: microseconds);

  var remainingTimers = [];
  var queue = new List.from(_timerQueue);
  _timerQueue.clear();
  queue
    .where((_TimerSpec spec) => spec.isActive)
    .forEach((_TimerSpec spec) {
      if (spec.periodic) {
        // We always add back the periodic timer unless it's cancelled.
        remainingTimers.add(spec);

        // Ignore ZERO duration ticks for periodic timers.
        if (tickDuration == Duration.ZERO) return;

        spec.elapsed += tickDuration;
        // Run the timer as many times as the timer priod fits into the tick.
        while (spec.elapsed >= spec.duration) {
          spec.elapsed -= spec.duration;
          microLeap();
          spec.fn(spec);
        }
      } else {
        spec.duration -= tickDuration;
        if (spec.duration <= Duration.ZERO) {
          microLeap();
          spec.fn();
        } else {
          remainingTimers.add(spec);
        }
      }
    });
  // Remaining timers should come before anything else scheduled after them.
  _timerQueue.insertAll(0, remainingTimers);
}

/**
 * Causes scheduleMicrotask calls to throw exceptions.
 *
 * This function is useful while debugging async tests: the exception
 * is thrown from the scheduleMicrotask call-site instead later in the test.
 */
noMoreAsync() {
  _noMoreAsync = true;
}

/**
 * Captures all scheduleMicrotask calls and newly created Timers
 * inside of a function.
 *
 * [async] will raise an exception if there are still active Timers
 * when the function completes.
 *
 * Use [clockTick] to process timers, and [microLeap] to process
 * scheduleMicrotask calls.
 *
 * NOTE: [async] will not return the result of [fn].
 *
 * Typically used within a test:
 *
 *     it('should be async', async(() {
 *       ...
 *     }));
 */
async(Function fn) => new FunctionComposition(_asyncOuter, fn);

_asyncOuter(Function fn) => () {
  _noMoreAsync = false;
  _asyncErrors.clear();
  _timerQueue.clear();
  var zoneSpec = new dart_async.ZoneSpecification(
      scheduleMicrotask: (_, __, ___, asyncFn) {
        if (_noMoreAsync) {
          throw ['scheduleMicrotask called after noMoreAsync()'];
        } else {
          _asyncQueue.add(asyncFn);
        }
      },
      createTimer: (_, __, ____, Duration duration, void f()) =>
          _createTimer(f, duration, false),
      createPeriodicTimer:
          (_, __, ___, Duration period, void f(dart_async.Timer timer)) =>
              _createTimer(f, period, true),
      handleUncaughtError: (_, __, ___, e, s) => _asyncErrors.add([e, s])
  );
  dart_async.runZoned(() {
      fn();
      microLeap();
    }, zoneSpecification: zoneSpec);

  _asyncErrors.forEach((e) {
    throw "During runZoned: ${e[0]}.  Stack:\n${e[1]}";
  });

  var activeTimers = _timerQueue.fold(0, (nb, _TimerSpec spec) {
    return spec.isActive ? nb + 1 : nb;
  });

  if (activeTimers > 0) {
    throw ["$activeTimers active timer(s) are still in the queue."];
  }
};

_createTimer(Function fn, Duration duration, bool periodic) {
  var timer = new _TimerSpec(fn, duration, periodic);
  _timerQueue.add(timer);
  return timer;
}

/**
 * Enforces synchronous code.  Any calls to scheduleMicrotask inside of 'sync'
 * will throw an exception.
 */
sync(Function fn) => new FunctionComposition(_syncOuter, fn);

_syncOuter(Function fn) => () {
  _asyncErrors.clear();

  dart_async.runZoned(fn, zoneSpecification: new dart_async.ZoneSpecification(
    scheduleMicrotask: (_, __, ___, asyncFn) {
        throw ['scheduleMicrotask called from sync function.'];
    },
    createTimer: (_, __, ____, Duration duration, void f()) {
        throw ['Timer created from sync function.'];
    },
    createPeriodicTimer:
        (_, __, ___, Duration period, void f(dart_async.Timer timer)) {
            throw ['periodic Timer created from sync function.'];
        },
    handleUncaughtError: (_, __, ___, e, s) => _asyncErrors.add([e, s])
    ));

  _asyncErrors.forEach((e) {
    throw "During runZoned: ${e[0]}.  Stack:\n${e[1]}";
  });
};

class _TimerSpec implements dart_async.Timer {
  Function fn;
  Duration duration;
  Duration elapsed = Duration.ZERO;
  bool periodic;
  bool isActive = true;

  _TimerSpec(this.fn, this.duration, this.periodic);

  void cancel() {
    isActive = false;
  }
}
