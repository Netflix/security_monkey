part of angular.core_internal;

/**
 * Compiles a string with markup into an expression. This service is used by the
 * HTML [Compiler] service for data binding.
 *
 *     var interpolate = ...; // injected
 *     var exp = interpolate('Hello {{name}}!');
 *     expect(exp).toEqual('"Hello "+(name|stringify)+"!"');
 */
@Injectable()
class Interpolate implements Function {
  var _cache = {};
  /**
   * Compiles markup text into expression.
   *
   * - [template]: The markup text to interpolate in form `foo {{expr}} bar`.
   * - [mustHaveExpression]: if set to true then the interpolation string must
   *   have embedded expression in order to return an expression. Strings with
   *   no embedded expression will return null.
   * - [startSymbol]: The symbol to start interpolation. '{{' by default.
   * - [endSymbol]: The symbol to end interpolation. '}}' by default.
   */

  String call(String template, [bool mustHaveExpression = false,
              String startSymbol = '{{', String endSymbol = '}}']) {
    if (mustHaveExpression == false && startSymbol == '{{' && endSymbol == '}}') {
      // cachable
      return _cache.putIfAbsent(template, () => _call(template, mustHaveExpression, startSymbol, endSymbol));
    }
    return _call(template, mustHaveExpression, startSymbol, endSymbol);
  }

  String _call(String template, [bool mustHaveExpression = false,
              String startSymbol, String endSymbol]) {
    if (template == null || template.isEmpty) return "";

    final startLen = startSymbol.length;
    final endLen = endSymbol.length;
    final length = template.length;

    int startIdx;
    int endIdx;
    int index = 0;

    bool hasInterpolation = false;

    String exp;
    final expParts = <String>[];

    while (index < length) {
      startIdx = template.indexOf(startSymbol, index);
      endIdx = template.indexOf(endSymbol, startIdx + startLen);
      if (startIdx != -1 && endIdx != -1) {
        if (index < startIdx) {
          // Empty strings could be stripped thanks to the stringify
          // formatter
          expParts.add(_wrapInQuotes(template.substring(index, startIdx)));
        }
        expParts.add('(' + template.substring(startIdx + startLen, endIdx) +
        '|stringify)');

        index = endIdx + endLen;
        hasInterpolation = true;
      } else {
        // we did not find any interpolation, so add the remainder
        expParts.add(_wrapInQuotes(template.substring(index)));
        break;
      }
    }

    return !mustHaveExpression || hasInterpolation ? expParts.join('+') : null;
  }

  String _wrapInQuotes(String s){
    final escaped = s.replaceAll(r'\', r'\\').replaceAll(r'"', r'\"');
    return '"$escaped"';
  }
}
