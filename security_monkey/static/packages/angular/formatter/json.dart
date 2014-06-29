part of angular.formatter_internal;

/**
 * Converts an object into a JSON string.
 *
 * This formatter is mostly useful for debugging.
 *
 * Note that the object to convert must be directly encodable to JSON (a
 * number, boolean, string, null, list or a map with string keys).  To convert other objects, the
 * [toEncodable](http://api.dartlang.org/apidocs/channels/stable/dartdoc-viewer/dart-convert
 * .JsonCodec#id_encode) function must be used first.
 *
 * # Usage
 *
 *     json_expression | json
 */
@Formatter(name:'json')
class Json implements Function {
  String call(jsonObj) => JSON.encode(jsonObj);
}
