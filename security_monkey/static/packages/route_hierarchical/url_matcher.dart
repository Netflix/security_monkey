library url_matcher;

import 'src/utils.dart';

/**
 * A reversible URL matcher interface.
 */
abstract class UrlMatcher extends Comparable<UrlMatcher> {
  /**
   * Attempts to match a given URL. If match is successful then returns an
   * instance or [UrlMatch], otherwise returns [null].
   */
  UrlMatch match(String url);

  /**
   * Reverses (reconstructs) a URL from optionally provided parameters map
   * and a tail.
   */
  String reverse({Map parameters, String tail});

  /**
   * Returns a list of named parameters in the URL.
   */
  List<String> urlParameterNames();

  /**
   * Returns a value which is:
   * * negative if this matcher should be tested before another.
   * * zero if this matcher and another can be tested in no particular order.
   * * positive if this matcher should be tested after another.
   */
  int compareTo(UrlMatcher other);
}

/**
 * Object representing a successful URL match.
 */
class UrlMatch {
  /// Matched section of the URL
  final String match;

  /// Remaining unmatched suffix
  final String tail;

  final Map parameters;

  UrlMatch(this.match, this.tail, this.parameters);

  bool operator ==(UrlMatch other) =>
    other is UrlMatch &&
    other.match == match &&
    other.tail == tail &&
    mapsShallowEqual(other.parameters, parameters);

  int get hashCode => 13 * match.hashCode + 101 * tail.hashCode + 199 * parameters.hashCode;

  String toString() => '{$match, $tail, $parameters}';
}
