part of angular.formatter_internal;

/**
 * Converts a string to uppercase.
 *
 * # Usage:
 *
 *     expression | uppercase
 */
@Formatter(name:'uppercase')
class Uppercase implements Function {
  call(String text) => text == null ? text : text.toUpperCase();
}
