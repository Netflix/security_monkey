part of angular.formatter_internal;

/**
 * Converts a string to lowercase.
 *
 * # Usage
 *
 *     expression | lowercase
 */
@Formatter(name:'lowercase')
class Lowercase implements Function {
  call(String text) => text == null ? text : text.toLowerCase();
}
