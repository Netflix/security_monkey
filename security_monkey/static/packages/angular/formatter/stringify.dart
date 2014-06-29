part of angular.formatter_internal;

/**
 * Converts an object to a string.
 *
 * Null objects are converted to an empty string.
 *
 *
 * # Usage:
 *
 *     expression | stringify
 */
@Formatter(name:'stringify')
class Stringify implements Function {
  String call(obj) => obj == null ? "" : obj.toString();
}
