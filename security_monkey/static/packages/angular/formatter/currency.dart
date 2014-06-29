part of angular.formatter_internal;

/**
 * Formats a number as a currency (for example $1,234.56).
 *
 * When no currency symbol is provided, '$' is used. For more on formatters,
 * see the [angular:formatter](#angular-formatter) library.
 *
 *
 * # Usage
 *
 *     expression | currency[:symbol[:leading]]
 *
 * # Example
 *
 *     {{ 1234 | currency }}                 // output is $1,234.00
 *     {{ 1234 | currency:'CAD' }}           // output is CAD1,234.00
 *     {{ 1234 | currency:'CAD':false }}     // output is 1,234.00CAD
 *
 *
 */
@Formatter(name:'currency')
class Currency implements Function {

  var _nfs = new Map<String, NumberFormat>();

  /**
   *  Format a number as a currency.
   *
   *  - `value`: the value to format as currency.
   *  - `symbol`: the currency symbol to use. If no symbol is specified, `$` is used.
   *  - `leading`: false places the symbol after the number instead of before
   *     it. (By default, leading is true.)
   */
  call(value, [symbol = r'$', leading = true]) {
    if (value is String) value = double.parse(value);
    if (value is! num) return value;
    if (value.isNaN) return '';
    var verifiedLocale = Intl.verifiedLocale(Intl.getCurrentLocale(), NumberFormat.localeExists);
    var nf = _nfs[verifiedLocale];
    if (nf == null) {
      nf = new NumberFormat();
      nf.minimumFractionDigits = 2;
      nf.maximumFractionDigits = 2;
      _nfs[verifiedLocale] = nf;
    }
    var neg = value < 0;
    if (neg) value = -value;
    var before = neg ? '(' : '';
    var after = neg ? ')' : '';
    return leading ?
        '$before$symbol${nf.format(value)}$after' :
        '$before${nf.format(value)}$symbol$after';
  }
}
