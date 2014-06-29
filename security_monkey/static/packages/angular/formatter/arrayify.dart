part of angular.formatter_internal;

/**
 * Transforms a Map into an array so that the map can be used with `ng-repeat`.
 *
 * # Example
 *
 *     <div ng-repeat="item in {'key1': 'value1', 'key2':'value2'} | arrayify">
 *       {{item.key}}: {{item.value}}
 *     </div>
 */
@Formatter(name:'arrayify')
class Arrayify implements Function {
  List<_KeyValue> call(Map inputMap) {
    if (inputMap == null) return null;
    List<_KeyValue> result = [];
    inputMap.forEach((k, v) => result.add(new _KeyValue(k, v)));
    return result;
  }
}

class _KeyValue<K, V> {
  K key;
  V value;

  _KeyValue(this.key, this.value);
}
