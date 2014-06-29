part of angular.directive;

/**
 * The `ngRepeat` directive instantiates a template once per item from a
 * collection. Each template instance gets its own scope, where the given loop
 * variable is set to the current collection item, and `$index` is set to the
 * item index or key.
 *
 * Special properties are exposed on the local scope of each template instance,
 * including:
 *
 *   * `$index` ([:num:]) the iterator offset of the repeated element
 *      (0..length-1)
 *   * `$first`  ([:bool:]) whether the repeated element is first in the
 *      iterator.
 *   * `$middle` ([:bool:]) whether the repeated element is between the first
 *      and last in the iterator.
 *   * `$last` ([:bool:]) whether the repeated element is last in the iterator.
 *   * `$even` ([:bool:]) whether the iterator position `$index` is even.
 *   * `$odd` ([:bool:]) whether the iterator position `$index` is odd.
 *
 *
 * [repeat_expression] ngRepeat The expression indicating how to enumerate a
 * collection. These formats are currently supported:
 *
 *   * `variable in expression` – where variable is the user defined loop
 *   variable and `expression` is a scope expression giving the collection to
 *   enumerate.
 *
 *     For example: `album in artist.albums`.
 *
 *   * `variable in expression track by tracking_expression` – You can also
 *   provide an optional tracking function which can be used to associate the
 *   objects in the collection with the DOM elements. If no tracking function is
 *   specified the ng-repeat associates elements by identity in the collection.
 *   It is an error to have more than one tracking function to resolve to the
 *   same key. (This would mean that two distinct objects are mapped to the same
 *   DOM element, which is not possible.)  Formatters should be applied to the
 *   expression, before specifying a tracking expression.
 *
 *     For example: `item in items` is equivalent to `item in items track by
 *     $id(item)`. This implies that the DOM elements will be associated by item
 *     identity in the array.
 *
 *     For example: `item in items track by $id(item)`. A built in `$id()`
 *     function can be used to assign a unique `$$hashKey` property to each item
 *     in the array. This property is then used as a key to associated DOM
 *     elements with the corresponding item in the array by identity. Moving the
 *     same object in array would move the DOM element in the same way in the
 *     DOM.
 *
 *     For example: `item in items track by item.id` is a typical pattern when
 *     the items come from the database. In this case the object identity does
 *     not matter. Two objects are considered equivalent as long as their `id`
 *     property is same.
 *
 *     For example: `item in items | filter:searchText track by item.id` is a
 *     pattern that might be used to apply a formatter to items in conjunction with
 *     a tracking expression.
 *
 * # Example:
 *
 *     <ul>
 *       <li ng-repeat="item in ['foo', 'bar', 'baz']">{{item}}</li>
 *     </ul>
 */

@Decorator(
    children: Directive.TRANSCLUDE_CHILDREN,
    selector: '[ng-repeat]',
    map: const {'.': '@expression'})
class NgRepeat {
  static RegExp _SYNTAX = new RegExp(r'^\s*(.+)\s+in\s+(.*?)\s*(?:track\s+by\s+(.+)\s*)?(\s+lazily\s*)?$');
  static RegExp _LHS_SYNTAX = new RegExp(r'^(?:([$\w]+)|\(([$\w]+)\s*,\s*([$\w]+)\))$');

  final ViewPort _viewPort;
  final BoundViewFactory _boundViewFactory;
  final Scope _scope;
  final Parser _parser;
  final FormatterMap formatters;

  String _expression;
  String _valueIdentifier;
  String _keyIdentifier;
  String _listExpr;
  List<_Row> _rows;
  Function _generateId = (key, value, index) => value;
  Watch _watch;

  NgRepeat(this._viewPort, this._boundViewFactory, this._scope,
           this._parser, this.formatters);

  set expression(value) {
    assert(value != null);
    _expression = value;
    if (_watch != null) _watch.remove();

    Match match = _SYNTAX.firstMatch(_expression);
    if (match == null) {
      throw "[NgErr7] ngRepeat error! Expected expression in form of '_item_ "
          "in _collection_[ track by _id_]' but got '$_expression'.";
    }

    _listExpr = match.group(2);

    var trackByExpr = match.group(3);
    if (trackByExpr != null) {
      Expression trackBy = _parser(trackByExpr);
      _generateId = ((key, value, index) {
        final context = <String, Object>{}
            ..[_valueIdentifier] = value
            ..[r'$index'] = index
            ..[r'$id'] = (obj) => obj;
        if (_keyIdentifier != null) context[_keyIdentifier] = key;
        return relaxFnArgs(trackBy.eval)(new ScopeLocals(_scope.context,
            context));
      });
    }

    var assignExpr = match.group(1);
    match = _LHS_SYNTAX.firstMatch(assignExpr);
    if (match == null) {
      throw "[NgErr8] ngRepeat error! '_item_' in '_item_ in _collection_' "
          "should be an identifier or '(_key_, _value_)' expression, but got "
          "'$assignExpr'.";
    }

    _valueIdentifier = match.group(3);
    if (_valueIdentifier == null) _valueIdentifier = match.group(1);
    _keyIdentifier = match.group(2);

    _watch = _scope.watch(
        _listExpr,
        (CollectionChangeRecord changes, _) {
          _onChange((changes is CollectionChangeRecord) ? changes : null);
        },
        collection: true,
        formatters: formatters
    );
  }

  // Computes and executes DOM changes when the item list changes
  void _onChange(CollectionChangeRecord changes) {
    final iterable = (changes == null) ? const [] : changes.iterable;
    final int length = (changes == null) ? 0 : changes.length;
    final rows = new List<_Row>(length);
    final changeFunctions = new List<Function>(length);
    final removedIndexes = <int>[];
    final int domLength = _rows == null ? 0 : _rows.length;
    final leftInDom = new List.generate(domLength, (i) => domLength - 1 - i);
    var domIndex;

    var addRow = (int index, value, View previousView) {
      var childContext = _updateContext(new PrototypeMap(_scope.context), index,
          length)..[_valueIdentifier] = value;
      var childScope = _scope.createChild(childContext);
      var view = _boundViewFactory(childScope);
      var nodes = view.nodes;
      rows[index] = new _Row(_generateId(index, value, index))
          ..view = view
          ..scope = childScope
          ..nodes = nodes
          ..startNode = nodes.first
          ..endNode = nodes.last;
      _viewPort.insert(view, insertAfter: previousView);
    };

    // todo(vicb) refactor once GH-774 gets fixed
    if (_rows == null) {
      _rows = new List<_Row>(length);
      for (var i = 0; i < length; i++) {
        changeFunctions[i] = (index, previousView) {
          addRow(index, iterable.elementAt(i), previousView);
        };
      }
    } else {
      if (changes == null) {
        _rows.forEach((row) {
          row.scope.destroy();
          _viewPort.remove(row.view);
        });
        leftInDom.clear();
      } else {
        changes.forEachRemoval((CollectionChangeItem removal) {
          var index = removal.previousIndex;
          var row = _rows[index];
          row.scope.destroy();
          _viewPort.remove(row.view);
          leftInDom.removeAt(domLength - 1 - index);
        });

        changes.forEachAddition((CollectionChangeItem addition) {
          changeFunctions[addition.currentIndex] = (index, previousView) {
            addRow(index, addition.item, previousView);
          };
        });

        changes.forEachMove((CollectionChangeItem move) {
          var previousIndex = move.previousIndex;
          var value = move.item;
          changeFunctions[move.currentIndex] = (index, previousView) {
            var previousRow = _rows[previousIndex];
            var childScope = previousRow.scope;
            var childContext = _updateContext(childScope.context, index, length);
            if (!identical(childScope.context[_valueIdentifier], value)) {
              childContext[_valueIdentifier] = value;
            }
            rows[index] = _rows[previousIndex];
            // Only move the DOM node when required
            if (domIndex < 0 || leftInDom[domIndex] != previousIndex) {
              _viewPort.move(previousRow.view, moveAfter: previousView);
              leftInDom.remove(previousIndex);
            }
            domIndex--;
          };
        });
      }
    }

    var previousView = null;
    domIndex = leftInDom.length - 1;
    for(var targetIndex = 0; targetIndex < length; targetIndex++) {
      var changeFn = changeFunctions[targetIndex];
      if (changeFn == null) {
        rows[targetIndex] = _rows[targetIndex];
        domIndex--;
        // The element has not moved but `$last` and `$middle` might still need
        // to be updated
        _updateContext(rows[targetIndex].scope.context, targetIndex, length);
      } else {
        changeFn(targetIndex, previousView);
      }
      previousView = rows[targetIndex].view;
    }

    _rows = rows;
  }

  PrototypeMap _updateContext(PrototypeMap context, int index, int length) {
    var first = (index == 0);
    var last = (index == length - 1);
    return context
        ..[r'$index'] = index
        ..[r'$first'] = first
        ..[r'$last'] = last
        ..[r'$middle'] = !(first || last)
        ..[r'$odd'] = index.isOdd
        ..[r'$even'] = index.isEven;
  }
}

class _Row {
  final id;
  Scope scope;
  View view;
  dom.Element startNode;
  dom.Element endNode;
  List<dom.Element> nodes;

  _Row(this.id);
}
