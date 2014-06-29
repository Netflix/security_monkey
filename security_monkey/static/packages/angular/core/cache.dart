part of angular.core_internal;

class CacheStats {
  final int capacity;
  final int size;
  final int hits;
  final int misses;
  CacheStats(this.capacity, this.size, this.hits, this.misses);
  String toString() =>
      "[CacheStats: capacity: $capacity, size: $size, hits: $hits, misses: $misses]";
}


/**
 * The Cache interface.
 */
abstract class Cache<K, V> {
  /**
   * Returns the value for `key` from the cache.  If `key` is not in the cache,
   * returns `null`.
   */
  V get(K key);
  /**
   * Inserts/Updates the `key` in the cache with `value` and returns the value.
   */
  V put(K key, V value);
  /**
   * Removes `key` from the cache.  If `key` isn't present in the cache, does
   * nothing.
   */
  V remove(K key);
  /**
   * Removes all entries from the cache.
   */
  void removeAll();
  int get capacity;
  int get size;
  CacheStats stats();
}


/**
 * An unbounded cache.
 */
class UnboundedCache<K, V> implements Cache<K, V> {
  Map<K, V> _entries = <K, V>{};
  int _hits = 0;
  int _misses = 0;

  V get(K key) {
    V value = _entries[key];
    if (value != null || _entries.containsKey(key)) {
      ++_hits;
    } else {
      ++_misses;
    }
    return value;
  }
  V put(K key, V value) => _entries[key] = value;
  V remove(K key) => _entries.remove(key);
  void removeAll() => _entries.clear();
  int get capacity => 0;
  int get size => _entries.length;
  CacheStats stats() => new CacheStats(capacity, size, _hits, _misses);
  // Debugging helper.
  String toString() => "[$runtimeType: size=${_entries.length}, items=$_entries]";
}


/**
 * Simple LRU cache.
 *
 * TODO(chirayu):
 * - add docs
 * - add tests
 * - should stringify keys?
 */
class LruCache<K, V> extends Cache<K, V> {
  final _entries = new LinkedHashMap<K, V>();
  int _capacity;
  int _hits = 0;
  int _misses = 0;

  LruCache({int capacity}) {
    this._capacity = capacity;
  }

  V get(K key) {
    V value = _entries[key];
    if (value != null || _entries.containsKey(key)) {
      ++_hits;
      // refresh
      _entries.remove(key);
      _entries[key] = value;
    } else {
      ++_misses;
    }
    return value;
  }

  V put(K key, V value) {
    // idempotent.  needed to refresh an existing key.
    _entries.remove(key);
    _entries[key] = value;
    if (_capacity != null && _capacity < _entries.length) {
      // drop oldest entry when at capacity
      // _entries.keys.first is fairly cheap - 2 new calls.
      _entries.remove(_entries.keys.first);
    }
    return value;
  }

  V remove(K key) => _entries.remove(key);
  void removeAll() => _entries.clear();
  int get capacity => _capacity;
  int get size => _entries.length;
  CacheStats stats() => new CacheStats(capacity, size, _hits, _misses);
  // Debugging helper.
  String toString() => "[$runtimeType: capacity=$capacity, size=$size, items=$_entries]";
}
