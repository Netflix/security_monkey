part of angular.formatter_internal;

// Too bad you can't stick typedef's inside a class.
typedef bool _Predicate(e);
typedef bool _Equals(a, b);

/**
 * Selects a subset of items from the provided [List] and returns it as a new
 * [List].
 *
 * # Usage
 *
 *      filter:expression[:comparator]
 *
 * In addition to the expression, which is used to select a subset from the list,
 * you can also specify a comparator to specify how the operation is performed. 
 *
 * The expression can be of the following types:
 *
 * - [String], [bool] and [num]:  Only items in the list that directly
 *   match this expression, items that are Maps with any value matching this
 *   item, and items that are lists containing a matching items are returned.
 *
 * - [Map]:  This defines a pattern map.  Filters specific properties on objects
 *   contained in the input list.  For example `{name:"M", phone:"1"}` predicate
 *   will return a list of items which have property `name` containing "M" and
 *   property `phone` containing "1".  A special property name, `$`, can be used
 *   (as in `{$: "text"}`) to accept a match against any property of the object.
 *   That's equivalent to the simple substring match with a `String` as
 *   described above.
 *
 * - [Function]:  This allows you to supply a custom function to filter the
 *   List.  The function is called for each element of the List.  The returned
 *   List contains exactly those elements for which this function returned
 *   `true`.
 *
 *
 * The comparator is optional and can be one of the following:
 *
 * - `bool comparator(expected, actual)`:  The function will be called with the
 *   object value and the predicate value to compare and should return true if
 *   the item should be included in filtered result.
 *
 * - `true`:  Specifies that only identical objects matching the expression
 *   exactly should be considered matches.  Two strings are considered identical
 *   if they are equal.  Two numbers are considered identical if they are either
 *   equal or both are `NaN`.  All other objects are identical iff
 *   identical(expected, actual) is true.
 *
 * - `false|null`:  Specifies case insensitive substring matching.
 *
 *
 * # Example ([view in plunker](http://plnkr.co/edit/6Mxz6r?p=info)):
 *
 *     // main.dart
 *     import 'package:angular/angular.dart';
 *
 *     @Decorator(selector: '[toy-data]')
 *     class ToyData {
 *       ToyData(Scope scope) {
 *         scope.friends = [{'name':'John',     'phone':'555-1276'},
 *                          {'name':'Mary',     'phone':'800-BIG-MARY'},
 *                          {'name':'Mike',     'phone':'555-4321'},
 *                          {'name':'Adam',     'phone':'555-5678'},
 *                          {'name':'Julie',    'phone':'555-8765'},
 *                          {'name':'Juliette', 'phone':'555-5678'}];
 *       }
 *     }
 *
 *     main() {
 *       ngBootstrap([new AngularModule()..bind(ToyData)], 'html');
 *     }
 *
 * and
 *
 *     <!-- index.html -->
 *     <html>
 *       <head>
 *         <script src="packages/browser/dart.js"></script>
 *         <script src="main.dart" type="application/dart"></script>
 *       </head>
 *       <body toy-data>
 *         Search: <input type="text" ng-model="searchText">
 *         <table id="searchTextResults">
 *           <tr><th>Name</th><th>Phone</th></tr>
 *           <tr ng-repeat="friend in friends | filter:searchText">
 *             <td>{{friend.name}}</td>
 *             <td>{{friend.phone}}</td>
 *           </tr>
 *         </table>
 *         <hr>
 *         Any: <input type="text" ng-model="search.$"> <br>
 *         Name only <input type="text" ng-model="search.name"><br>
 *         Phone only <input type="text" ng-model="search.phone"><br>
 *         <table id="searchObjResults">
 *           <tr><th>Name</th><th>Phone</th></tr>
 *           <tr ng-repeat="friend in friends | filter:search:strict">
 *             <td>{{friend.name}}</td>
 *             <td>{{friend.phone}}</td>
 *           </tr>
 *         </table>
 *       </body>
 *     </html>
 */
@Formatter(name: 'filter')
class Filter implements Function {
  Parser _parser;
  _Equals _comparator;
  _Equals _stringComparator;

  static _nop(e) => e;
  static _ensureBool(val) => (val is bool && val);
  static _isSubstringCaseInsensitive(String a, String b) =>
      a != null && b != null && a.toLowerCase().contains(b.toLowerCase());
  static _identical(a, b) => identical(a, b) ||
                             (a is String && b is String && a == b) ||
                             (a is num && b is num && a.isNaN && b.isNaN);

  Filter(this._parser);

  void _configureComparator(var comparatorExpression) {
    if (comparatorExpression == null || comparatorExpression == false) {
      _stringComparator = _isSubstringCaseInsensitive;
      _comparator = _defaultComparator;
    } else if (comparatorExpression == true) {
      _stringComparator = _identical;
      _comparator = _defaultComparator;
    } else if (comparatorExpression is _Equals) {
      _comparator = (a, b) => _ensureBool(comparatorExpression(a, b));
    } else {
      _comparator = null;
    }
  }

  // Preconditions
  // - what: NOT a Map
  // - item: neither a Map nor a List
  bool _defaultComparator(var item, var what) {
    if (what == null) {
      return false;
    } else if (item == null) {
      return what == '';
    } else if (what is String && what.startsWith('!')) {
      return !_search(item, what.substring(1));
    } else if (item is String) {
      return (what is String) && _stringComparator(item, what);
    } else if (item is bool) {
      if (what is bool) {
        return item == what;
      } else if (what is String) {
        what = (what as String).toLowerCase();
        return item ? (what == "true"  || what == "yes" || what == "on")
                    : (what == "false" || what == "no"  || what == "off");
      } else {
        return false;
      }
    } else if (item is num) {
      if (what is num) {
        return item == what || (item.isNaN && what.isNaN);
      } else {
        return what is String && _stringComparator('$item', what);
      }
    } else {
      return false; // Unsupported item type.
    }
  }

  bool _search(var item, var what) {
    if (what is Map) {
      return what.keys.every((key) => _search(
              (key == r'$') ? item : _parser(key).eval(item), what[key]));
    } else if (item is Map) {
      return item.keys.any((k) => !k.startsWith(r'$') && _search(item[k], what));
    } else if (item is List) {
      return item.any((i) => _search(i, what));
    } else {
      return _comparator(item, what);
    }
  }

  _Predicate _toPredicate(var expression) {
    if (expression is _Predicate) {
      return (item) => _ensureBool(expression(item));
    } else if (_comparator == null) {
      return (item) => false; // Bad comparator → no items for you!
    } else {
      return (item) => _search(item, expression);
    }
  }

  List call(List items, var expression, [var comparator]) {
    if (expression == null) {
      return items.toList(growable: false); // Missing expression → passthrough.
    } else if (expression is! Map && expression is! Function &&
               expression is! String && expression is! bool &&
               expression is! num) {
      return const []; // Bad expression → no items for you!
    }
    _configureComparator(comparator);
    List results = items.where(_toPredicate(expression)).toList(growable: false);
    _comparator = null;
    return results;
  }
}
