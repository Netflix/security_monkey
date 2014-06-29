part of angular.formatter_internal;

typedef dynamic _Mapper(dynamic e);

/**
 * Orders the the elements of a list using a predicate.
 *
 * # Usage
 *
 *      expression | orderBy:predicate[:true]
 *
 * The input to orderBy must be an [Iterable] object. The predicate may be specified as:
 *
 * - **a string**: a string containing an expression, such as "user.lastName", used to order the list.
 * - **a custom callable expression**: an expression that will be called to transform the element
 *   before a sort.
 * - **a list**: the list may consist of either strings or callable expressions.  A list expression
 *   indicates a list of fallback expressions to use when a comparision results in the items
 *   being equal.
 *
 * If the expression is explicitly empty(`orderBy:''`), the elements are sorted in
 * ascending order, using the default comparator, `+`.
 *
 * A string expression in the predicate can be prefixed to indicate sort order:
 *
 * - `+`: sort the elements in ascending order. This is the default.
 * - `-`: sort the elements in descending order.
 *
 * Alternately, by appending `true`, you can set "descending order" to true, which has the same effect as the `-`
 * prefix.
 *
 * # Examples
 *
 * ## Example 1: Simple array and single/empty expression.
 *
 * Assume that you have an array on scope called `colors` and that it has a list
 * of these strings – `['red', 'blue', 'green']`.  You might sort these in
 * ascending order this way:
 *
 *     Colors: <ul>
 *       <li ng-repeat="color in colors | orderBy:''">{{color}}</li>
 *     </ul>
 *
 * That would result in:
 *
 *     <ul>
 *       <li>blue</li>
 *       <li>green</li>
 *       <li>red</li>
 *     <ul>
 *
 * The empty string expression, `''`, here signifies sorting in ascending order
 * using the default comparator.  Using `'+'` would also work, as the `+` prefix
 * is implied.
 *
 * To sort in descending order, you would use the `'-'` prefix.
 *
 *     Colors: <ul>
 *       <li ng-repeat="color in colors | orderBy:'-'">{{color}}</li>
 *     </ul>
 *
 * For this simple example, you could have also provided `true` as the addition
 * optional parameter which requests a reverse order sort to get the same
 * result.
 *
 *     <!-- Same result (descending order) as previous snippet. -->
 *     Colors: <ul>
 *       <li ng-repeat="color in colors | orderBy:'':true">{{color}}</li>
 *     </ul>
 *
 * ## Example 2: Complex objects, single expression.
 *
 * You may provide a more complex expression to sort non-primitive values or
 * if you want to sort on a decorated/transformed value.
 *
 * e.g. Support you have a list `users` that looks like this:
 *
 *     authors = [
 *       {firstName: 'Emily',   lastName: 'Bronte'},
 *       {firstName: 'Mark',    lastName: 'Twain'},
 *       {firstName: 'Jeffrey', lastName: 'Archer'},
 *       {firstName: 'Isaac',   lastName: 'Asimov'},
 *       {firstName: 'Oscar',   lastName: 'Wilde'},
 *     ];
 *
 * If you want to list the authors sorted by `lastName`, you would use
 *
 *     <li ng-repeat="author in authors | orderBy:'lastName'">
 *       {{author.lastName}}, {{author.firstName}}
 *     </li>
 *
 * The string expression, `'lastName'`, indicates that the sort should be on the
 * `lastName` property of each item.
 *
 * Using the lesson from the previous example, you may sort in reverse order of
 * lastName using either of the two methods.
 *
 *     <!-- reverse order of last names -->
 *     <li ng-repeat="author in authors | orderBy:'-lastName'">
 *     <!-- also does the same thing -->
 *     <li ng-repeat="author in authors | orderBy:'lastName':true">
 *
 * Note that, while we only discussed string expressions, such as `"lastName"`
 * or the empty string, you can also directly provide a custom callable that
 * will be called to transform the element before a sort.
 *
 *     <li ng-repeat="author in authors | orderBy:getAuthorId">
 *
 * In the previous snippet, `getAuthorId` would evaluate to a callable when
 * evaluated on the [Scope](#angular-core.Scope) of the `<li>` element.  That callable is called once
 * for each element in the list (i.e. each author object) and the sort order is
 * determined by the sort order of the value mapped by the callable.
 *
 * ## Example 3: List expressions
 *
 * Both a string expression and the callable expression are simple versions of
 * the more general list expression.  You may pass a list as the orderBy
 * expression and this list may consist of either of the string or callable
 * expressions you saw in the previous examples.  A list expression indicates
 * a list of fallback expressions to use when a comparision results in the items
 * being equal.
 *
 * For example, one might want to sort the authors list, first by last name and
 * then by first name when the last names are equal.  You would do that like
 * this:
 *
 *     <li ng-repeat="author in authors | orderBy:['lastName', 'firstName']">
 *
 * The items in such a list may either be string expressions or callables.  The
 * list itself might be provided as an expression that is looked up on the scope
 * chain.
 */
@Formatter(name: 'orderBy')
class OrderBy implements Function {
  Parser _parser;

  OrderBy(this._parser);

  static _nop(e) => e;
  static bool _isNonZero(int n) => (n != 0);
  static int _returnZero() => 0;
  static int _defaultComparator(a, b) => Comparable.compare(a, b);
  static int _reverseComparator(a, b) => _defaultComparator(b, a);

  static int _compareLists(List a, List b, List<Comparator> comparators) {
    return new Iterable.generate(a.length, (i) => comparators[i](a[i], b[i]))
        .firstWhere(_isNonZero, orElse: _returnZero);
  }

  static List _sorted(
      List items, List<_Mapper> mappers, List<Comparator> comparators, bool descending) {
    // Do the standard decorate-sort-undecorate aka Schwartzian dance since Dart
    // doesn't support a key/transform parameter to sort().
    // Ref: http://en.wikipedia.org/wiki/Schwartzian_transform
    mapper(e) => mappers.map((m) => m(e)).toList(growable: false);
    List decorated = items.map(mapper).toList(growable: false);
    List<int> indices = new Iterable.generate(decorated.length, _nop).toList(growable: false);
    comparator(i, j) => _compareLists(decorated[i], decorated[j], comparators);
    indices.sort((descending) ? (i, j) => comparator(j, i) : comparator);
    return indices.map((i) => items[i]).toList(growable: false);
  }

  /**
   * Order a list by expression.
   *
   * - `expression`: String/Function or Array of String/Function.
   * - `descending`: When specified, use descending order. (The default is ascending order.)
   */
  List call(List items, var expression, [bool descending=false]) {
    if (items == null) {
      return null;
    }
    List expressions = null;
    if (expression is String || expression is _Mapper) {
      expressions = [expression];
    } else if (expression is List) {
      expressions = expression as List;
    }
    if (expressions == null || expressions.length == 0) {
      // AngularJS behavior.  You must have an expression to get any work done.
      return items;
    }
    int numExpressions = expressions.length;
    List<_Mapper> mappers = new List(numExpressions);
    List<Comparator> comparators = new List<Comparator>(numExpressions);
    for (int i = 0; i < numExpressions; i++) {
      expression = expressions[i];
      if (expression is String) {
        var strExp = expression as String;
        var desc = false;
        if (strExp.startsWith('-') || strExp.startsWith('+')) {
          desc = strExp.startsWith('-');
          strExp = strExp.substring(1);
        }
        comparators[i] = desc ? _reverseComparator : _defaultComparator;
        if (strExp == '') {
          mappers[i] = _nop;
        } else {
          Expression parsed = _parser(strExp);
          mappers[i] = (e) => parsed.eval(e);
        }
      } else if (expression is _Mapper) {
        mappers[i] = (expression as _Mapper);
        comparators[i] = _defaultComparator;
      }
    }
    return _sorted(items, mappers, comparators, descending);
  }
}
