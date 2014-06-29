part of angular.formatter_internal;

/**
 * Formats a date value to a string based on the requested format.
 *
 * # Usage
 *
 *     date_expression | date[:format]
 *
 * `format` may be specified explicitly, or by using one of the following predefined shorthand:
 *
 *      FORMAT NAME        OUTPUT for en_US
 *     -------------  ---------------------------
 *      medium         Sep 3, 2010 12:05:08 PM
 *      short          9/3/10 12:05 PM
 *      fullDate       Friday, September 3, 2010
 *      longDate       September 3, 2010
 *      mediumDate     Sep 3, 2010
 *      shortDate      9/3/10
 *      mediumTime     12:05:08 PM
 *      shortTime      12:05 PM
 *
 * For more on explicit formatting of dates and date syntax, see the documentation for the
 * [DartFormat class](https://api.dartlang.org/apidocs/channels/stable/dartdoc-viewer/intl/intl.DateFormat).
 *
 * # Example
 *
 *     '2014-05-22' | date:'fullDate'     // "Thursday, May 22, 2014" for the en_US locale
 *
 */
@Formatter(name:'date')
class Date implements Function {
  static final _PATTERNS = const <String, dynamic> {
    'medium':     const [DateFormat.YEAR_ABBR_MONTH_DAY, DateFormat.HOUR_MINUTE_SECOND],
    'short':      const [DateFormat.YEAR_NUM_MONTH_DAY, DateFormat.HOUR_MINUTE],
    'fullDate':   DateFormat.YEAR_MONTH_WEEKDAY_DAY,
    'longDate':   DateFormat.YEAR_MONTH_DAY,
    'mediumDate': DateFormat.YEAR_ABBR_MONTH_DAY,
    'shortDate':  DateFormat.YEAR_NUM_MONTH_DAY,
    'mediumTime': DateFormat.HOUR_MINUTE_SECOND,
    'shortTime':  DateFormat.HOUR_MINUTE,
  };

  /// locale -> (format -> DateFormat)
  var _dfs = new Map<String, Map<String, DateFormat>>();

  /**
   * Format a value as a date.
   *
   *  - `date`:   value to format as a date. If no timezone is specified in the string input,
   *     the time is considered to be in the local timezone.
   *  - `format`: Either a named format, or an explicit format specification.  If no format is
   *     specified, mediumDate is used.
   *
   */
  dynamic call(Object date, [String format = 'mediumDate']) {
    if (date == '' || date == null) return date;
    if (date is String) date = DateTime.parse(date);
    if (date is num) date = new DateTime.fromMillisecondsSinceEpoch(date);
    if (date is! DateTime) return date;
    var verifiedLocale = Intl.verifiedLocale(Intl.getCurrentLocale(), DateFormat.localeExists);
    return _getDateFormat(verifiedLocale, format).format(date);
  }

  DateFormat _getDateFormat(String locale, String format) {
    _dfs.putIfAbsent(locale, () => <String, DateFormat>{});

    if (_dfs[locale][format] == null) {
      var pattern = _PATTERNS.containsKey(format) ? _PATTERNS[format] : format;
      if (pattern is !Iterable) pattern = [pattern];
      var df = new DateFormat();
      pattern.forEach((p) {
         df.addPattern(p);
      });
      if (format == "short" || format == "shortDate") {
        // "short" and "shortDate" formats use a 2-digit year
        df = new DateFormat(df.pattern.replaceAll(new RegExp('y+'), 'yy'));
      }
      _dfs[locale][format] = df;
    }
    return _dfs[locale][format];
  }
}
