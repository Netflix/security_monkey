part of angular.formatter_internal;

/**
 * Creates a new List or String containing only a prefix/suffix of the
 * elements.
 *
 * The number of elements to return is specified by the `limitTo` parameter.
 *
 * # Usage
 *
 *     expression | limitTo:number
 *
 * Where the input expression is a [List] or [String], and `limitTo` is:
 *
 * - **a positive integer**: return _number_ items from the beginning of the list or string
 * expression.
 * - **a negative integer**: return _number_ items from the end of the list or string expression.
 * - **`|limitTo|` greater than the size of the expression**: return the entire expression.
 * - **null** or all other cases: return an empty list or string.
 *
 * When operating on a [List], the returned list is always a copy even when all
 * the elements are being returned.
 *
 * # Examples
 *
 *     {{ 'abcdefghij' | limitTo: 4 }}       // output is 'abcd'
 *     {{ 'abcdefghij' | limitTo: -4 }}      // output is 'ghij'
 *     {{ 'abcdefghij' | limitTo: -100 }}    // output is 'abcdefghij'
 *
 *
 * This `ng-repeat` directive:
 *
 *     <li ng-repeat="i in 'abcdefghij' | limitTo:-2">{{i}}</li>
 *
 * produces the following:
 *
 *     <li>i</li>
 *     <li>j</li>
 */
@Formatter(name:'limitTo')
class LimitTo implements Function {
  Injector _injector;

  LimitTo(this._injector);

  dynamic call(dynamic items, [int limit]) {
    if (items == null) return null;
    if (limit == null) return const[];
    if (items is! List && items is! String) return items;
    int i = 0, j = items.length;
    if (limit > -1) {
      j = (limit > j) ? j : limit;
    } else {
      i = j + limit;
      if (i < 0) i = 0;
    }
    return items is String ?
        (items as String).substring(i, j) :
        (items as List).getRange(i, j).toList(growable: false);
  }
}
