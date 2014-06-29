part of angular.watch_group;

class PrototypeMap<K, V> implements Map<K,V> {
  final Map<K, V> prototype;
  final Map<K, V> self = new Map();

  PrototypeMap(this.prototype);

  void operator []=(name, value) {
    self[name] = value;
  }
  V operator [](name) => self.containsKey(name) ? self[name] : prototype[name];

  bool get isEmpty => self.isEmpty && prototype.isEmpty;
  bool get isNotEmpty => self.isNotEmpty || prototype.isNotEmpty;
  // todo(vbe) include prototype keys ?
  Iterable<K> get keys => self.keys;
  // todo(vbe) include prototype values ?
  Iterable<V> get values => self.values;
  int get length => self.length;

  void forEach(fn) {
    // todo(vbe) include prototype ?
    self.forEach(fn);
  }
  V remove(key) => self.remove(key);
  clear() => self.clear;
  // todo(vbe) include prototype ?
  bool containsKey(key) => self.containsKey(key);
  // todo(vbe) include prototype ?
  bool containsValue(key) => self.containsValue(key);
  void addAll(map) {
    self.addAll(map);
  }
  // todo(vbe) include prototype ?
  V putIfAbsent(key, fn) => self.putIfAbsent(key, fn);
}
