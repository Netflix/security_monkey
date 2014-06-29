// Copyright (c) 2013, the Dart project authors.  Please see the AUTHORS file
// for details. All rights reserved. Use of this source code is governed by a
// BSD-style license that can be found in the LICENSE file.

library route.url_pattern;

import 'url_matcher.dart';

// From the PatternCharacter rule here:
// http://ecma-international.org/ecma-262/5.1/#sec-15.10
// removed '( and ')' since we'll never escape them when not in a group
final _specialChars = new RegExp(r'[$.|+[\]{}^]');

UrlPattern urlPattern(String p) => new UrlPattern(p);

/**
 * A pattern, similar to a [RegExp], that is designed to match against URL
 * paths, easily return groups of a matched path, and produce paths from a list
 * of arguments - this is they are "reversible".
 *
 * `UrlPattern`s also allow for handling plain paths and URLs with a fragment in
 * a uniform way so that they can be used for client side routing on browsers
 * that support `window.history.pushState` as well as legacy browsers.
 *
 * The differences from a plain [RegExp]:
 *  * All non-literals must be in a group. Everything outside of a groups is
 *    considered a literal and special regex characters are escaped.
 *  * There can only be one match, and it must match the entire string. `^` and
 *    `$` are automatically added to the beginning and end of the pattern,
 *    respectively.
 *  * The pattern must be un-ambiguous, eg `(.*)(.*)` is not allowed at the
 *    top-level.
 *  * The hash character (#) matches both '#' and '/', and it is only allowed
 *    once per pattern. Hashes are not allowed inside groups.
 *
 * With those differences, `UrlPatterns` become much more useful for routing
 * URLs and constructing them, both on the client and server. The best practice
 * is to define your application's set of URLs in a shared library.
 *
 * urls.dart:
 *
 *     library urls;
 *
 *     final articleUrl = new UrlPattern(r'/articles/(\d+)');
 *
 * server.dart:
 *
 *     import 'urls.dart';
 *     import 'package:route/server.dart';
 *
 *     main() {
 *       var server = new HttpServer();
 *       server.addRequestHandler(matchesUrl(articleUrl), serveArticle);
 *     }
 *
 *     serveArticle(req, res) {
 *       var articleId = articleUrl.parse(req.path)[0];
 *       // ...
 *     }
 *
 * Use with older browsers
 * -----------------------
 *
 * Since '#' matches both '#' and '/' it can be used in as a path separator
 * between the "static" portion of your URL and the "dynamic" portion. The
 * dynamic portion would be the part that change when a user navigates to new
 * data that's loaded dynamically rather than loading a new page.
 *
 * In newer browsers that support `History.pushState()` an entire new path can
 * be pushed into the location bar without reloading the page. In older browsers
 * only the fragment can be changed without reloading the page. By matching both
 * characters, and by producing either, we can use pushState in newer browsers,
 * but fall back to fragments when necessary.
 *
 * Examples:
 *
 *     var pattern = new UrlPattern(r'/app#profile/(\d+)');
 *     pattern.matches('/app/profile/1234'); // true
 *     pattern.matches('/app#profile/1234'); // true
 *     pattern.reverse([1234], useFragment: true); // /app#profile/1234
 *     pattern.reverse([1234], useFragment: false); // /app/profile/1234
 */
class UrlPattern implements UrlMatcher, Pattern {
  final String pattern;
  RegExp _regex;
  bool _hasFragment;
  RegExp _baseRegex;

  UrlPattern(this.pattern) {
    _parse(pattern);
  }

  RegExp get regex => _regex;

  String reverse(Iterable args, {bool useFragment: false}) {
    var sb = new StringBuffer();
    var argsIter = args.iterator;

    int depth = 0;
    int groupCount = 0;
    bool escaped = false;

    for (int i = 0; i < pattern.length; i++) {
      var c = pattern[i];
      if (c == '\\' && escaped == false) {
        escaped = true;
      } else {
        if (c == '(') {
          if (escaped && depth == 0) {
            sb.write(c);
          }
          if (!escaped) depth++;
        } else if (c == ')') {
          if (escaped && depth == 0) {
            sb.write(c);
          } else if (!escaped) {
            if (depth == 0) throw new ArgumentError('unmatched parentheses');
            depth--;
            if (depth == 0) {
              // append the nth arg
              if (argsIter.moveNext()) {
                sb.write(argsIter.current.toString());
              } else {
                throw new ArgumentError('more groups than args');
              }
            }
          }
        } else if (depth == 0) {
          if (c == '#' && !useFragment) {
            sb.write('/');
          } else {
            sb.write(c);
          }
        }
        escaped = false;
      }
    }
    if (depth > 0) {
      throw new ArgumentError('unclosed group');
    }
    return sb.toString();
  }

  /**
   * Parses a URL path, or path + fragment, and returns the group matches.
   * Throws [ArgumentError] if this pattern does not match [path].
   */
  List<String> parse(String path) {
    var match = regex.firstMatch(path);
    if (match == null) {
      throw new ArgumentError('no match for $path');
    }
    var result = <String>[];
    for (int i = 1; i <= match.groupCount; i++) {
      result.add(match[i]);
    }
    return result;
  }

  UrlMatch match(String url) {
    var matches = allMatches(url);
    if (matches.isEmpty) {
      return null;
    }
    var match = matches.first;
    var tail = url.substring(match.group(0).length);
    Map parameters = new Map();
    for (var i = 0; i < match.groupCount; i++) {
      parameters[i] = match.group(i + 1);
    }
    return new UrlMatch(match.group(0), tail, parameters);
  }

  /**
   * Returns true if this pattern matches [path].
   */
  bool matches(String str) => _matches(regex, str);

  // TODO(justinfagnani): file bug for similar method to be added to Pattern
  bool _matches(Pattern p, String str) {
    var iter = p.allMatches(str).iterator;
    if (iter.moveNext()) {
      var match = iter.current;
      return (match.start == 0) && (match.end == str.length)
          && (!iter.moveNext());
    }
    return false;
  }

  /**
   * Returns true if the path portion of the pattern, the part before the
   * fragment, matches [str]. If there is no fragment in the pattern, this is
   * equivalent to calling [matches].
   *
   * This method is most useful on a server that is serving the HTML of a
   * single page app. Clients that don't support pushState will not send the
   * fragment to the server, so the server will have to handle just the path
   * part.
   */
  bool matchesNonFragment(String str) =>
      _hasFragment ? _matches(_baseRegex, str) : matches(str);

  Iterable<Match> allMatches(String str) => regex.allMatches(str);

  bool operator ==(other) =>
      (other is UrlPattern) && (other.pattern == pattern);

  int get hashCode => pattern.hashCode;

  String toString() => 'UrlPattern(${pattern.toString()})';

  _parse(String pattern) {
    var sb = new StringBuffer();
    int depth = 0;
    int lastGroupEnd = -2;
    bool escaped = false;

    sb.write('^');
    var chars = pattern.split('');
    for (var i = 0; i < chars.length; i++) {
      var c = chars[i];

      if (depth == 0) {
        // outside of groups, transform the pattern to matches the literal
        if (c == r'\') {
          if (escaped) {
            sb.write(r'\\');
          }
          escaped = !escaped;
        } else {
          if (_specialChars.hasMatch(c)) {
            sb.write('\\$c');
          } else if (c == '(') {
            if (escaped) {
              sb.write(r'\(');
            } else {
              sb.write('(');
              if (lastGroupEnd == i - 1) {
                throw new ArgumentError('ambiguous adjecent top-level groups');
              }
              depth = 1;
            }
          } else if (c == ')') {
            if (escaped) {
              sb.write(r'\)');
            } else {
              throw new ArgumentError('unmatched parenthesis');
            }
          } else if (c == '#') {
            _setBasePattern(sb.toString());
            sb.write('[/#]');
          } else {
            sb.write(c);
          }
          escaped = false;
        }
      } else {
        // in a group, don't modify the pattern, but track escaping and depth
        if (c == '(' && !escaped) {
          depth++;
        } else if (c == ')' && !escaped) {
          depth--;
          if (depth < 0) throw new ArgumentError('unmatched parenthesis');
          if (depth == 0) {
            lastGroupEnd = i;
          }
        } else if (c == '#') {
          // TODO(justinfagnani): what else should be banned in groups? '/'?
          throw new ArgumentError('illegal # inside group');
        }
        escaped = (c == r'\' && !escaped);
        sb.write(c);
      }
    }
    _regex = new RegExp(sb.toString());
  }

  void _setBasePattern(String basePattern) {
    if (_hasFragment == true) {
      throw new ArgumentError('multiple # characters');
    }
    _hasFragment = true;
    _baseRegex = new RegExp('$basePattern\$');
  }

  Match matchAsPrefix(String string, [int start = 0]) {
    throw new UnimplementedError('matchAsPrefix is not implemented');
  }

  List<String> urlParameterNames() {
    throw new UnimplementedError('urlParameterNames is not implemented');
  }

  int compareTo(UrlMatcher another) {
    throw new UnimplementedError('compareTo is not implemented');
  }
}
