library perf_api;

import 'dart:async';

/**
 * A simple profiler api.
 */
class Profiler {
  final Counters counters = new Counters();

  /**
   * Const constructor allows instances of this class to be used as a no-op
   * implementation.
   */
  const Profiler();

  /**
   * Starts a new timer for a given action [name]. A timer id will be
   * returned which can be used in [stopTimer] to stop the timer.
   *
   * [extraData] is additional information about the timed action. Implementing
   * profiler should not assume any semantic or syntactic structure of that
   * data and is free to ignore it in aggregate reports.
   */
  dynamic startTimer(String name, [dynamic extraData]) => null;

  /**
   * Stop a timer for a given [idOrName]. [idOrName] can either be a timer
   * identifier returned from [startTimer] or a timer name string. If [idOrName]
   * is invalid or timer for that [idOrName] was already stopped then
   * [ProfilerError] will be thrown. If [idOrName] is a String timer name then
   * the latest active timer with that name will be stopped.
   */
  void stopTimer(dynamic idOrName) {}

  /**
   * A simple zero-duration marker.
   */
  void markTime(String name, [dynamic extraData]) {}

  /**
   * Times execution of the [functionOrFuture]. Body can either be a no argument
   * function or a [Future]. If function, it is executed synchronously and its
   * return value is returned. If it's a Future, then timing is stopped when the
   * future completes either successfully or with error.
   */
  dynamic time(String name, functionOrFuture, [dynamic extraData]) {
    var id = startTimer(name, extraData);
    if (functionOrFuture is Function) {
      try {
        return functionOrFuture();
      } finally {
        stopTimer(id);
      }
    }
    if (functionOrFuture is Future) {
      return functionOrFuture.then(
          (v) {
            stopTimer(id);
            return v;
          },
          onError: (e) {
            stopTimer(id);
            throw e;
          });
    }
    throw new ProfilerError(
        'Invalid functionOrFuture or type ${functionOrFuture.runtimeType}');
  }
}

class Counters {

  final Map<String, int> _counters = <String, int>{};

  const Counters();

  /**
   * Increments the counter under [counterName] by [delta]. Default [delta]
   * is 1. If counter is not yet initilalized, its value is assumed to be 0.
   * [delta] is allowed to be negative and it is possible for the counter value
   * to become negative.
   */
  int increment(String counterName, [int delta = 1]) {
    _counters.putIfAbsent(counterName, _initWithZero);
    _counters[counterName] += delta;
    return _counters[counterName];
  }

  /**
   * Returns the current value of the counter. If the counter value is not
   * initialized then null is returned.
   */
  int operator [](String counterName) => _counters[counterName];

  /**
   * Sets a [value] for a [counterName]. Any previous value is overridden.
   */
  operator []=(String counterName, int value) => _counters[counterName] = value;

  /**
   * Returns an immutable map of all known counter values.
   */
  Map<String, int> get all => new _UnmodifiableMap(_counters);
}

int _initWithZero() => 0;

class ProfilerError extends Error {
  final String message;
  ProfilerError(String this.message);
  toString() => message;
}

class _UnmodifiableMap<K, V> implements Map<K, V> {
  final Map _map;

  const _UnmodifiableMap(this._map);

  bool containsValue(Object value) => _map.containsValue(value);

  bool containsKey(Object key) => _map.containsKey(key);

  V operator [](Object key) => _map[key];

  void operator []=(K key, V value) {
    throw new UnsupportedError("Cannot modify an unmodifiable map");
  }

  V putIfAbsent(K key, V ifAbsent()) {
    throw new UnsupportedError("Cannot modify an unmodifiable map");
  }

  addAll(Map other) {
    throw new UnsupportedError("Cannot modify an unmodifiable map");
  }

  V remove(Object key) {
    throw new UnsupportedError("Cannot modify an unmodifiable map");
  }

  void clear() {
    throw new UnsupportedError("Cannot modify an unmodifiable map");
  }

  void forEach(void f(K key, V value)) => _map.forEach(f);

  Iterable<K> get keys => _map.keys;

  Iterable<V> get values => _map.values;

  int get length => _map.length;

  bool get isEmpty => _map.isEmpty;

  bool get isNotEmpty => _map.isNotEmpty;
}
