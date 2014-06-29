library angular.watch_group;

import 'package:angular/change_detection/change_detection.dart';

part 'linked_list.dart';
part 'ast.dart';
part 'prototype_map.dart';

/**
 * A function that is notified of changes to the model.
 *
 * ReactionFn is a function implemented by the developer that executes when a change is detected
 * in a watched expression.
 *
 * * [value]: The current value of the watched expression.
 * * [previousValue]: The previous value of the watched expression.
 *
 * If the expression is watching a collection (a list or a map), then [value] is wrapped in
 * a [CollectionChangeItem] that lists all the changes.
 */
typedef void ReactionFn(value, previousValue);
typedef void ChangeLog(String expression, current, previous);

/**
 * Extend this class if you wish to pretend to be a function, but you don't know
 * number of arguments with which the function will get called with.
 */
abstract class FunctionApply {
  dynamic call() { throw new StateError('Use apply()'); }
  dynamic apply(List arguments);
}

/**
 * [WatchGroup] is a logical grouping of a set of watches. [WatchGroup]s are
 * organized into a hierarchical tree parent-children configuration.
 * [WatchGroup] builds upon [ChangeDetector] and adds expression (field chains
 * as in `a.b.c`) support as well as support function/closure/method (function
 * invocation as in `a.b()`) watching.
 */
class WatchGroup implements _EvalWatchList, _WatchGroupList {
  /** A unique ID for the WatchGroup */
  final String id;
  /**
   * A marker to be inserted when a group has no watches. We need the marker to
   * hold our position information in the linked list of all [Watch]es.
   */
  final _EvalWatchRecord _marker = new _EvalWatchRecord.marker();

  /** All Expressions are evaluated against a context object. */
  final Object context;

  /** [ChangeDetector] used for field watching */
  final ChangeDetectorGroup<_Handler> _changeDetector;
  /** A cache for sharing sub expression watching. Watching `a` and `a.b` will
  * watch `a` only once. */
  final Map<String, WatchRecord<_Handler>> _cache;
  final RootWatchGroup _rootGroup;

  /// STATS: Number of field watchers which are in use.
  int _fieldCost = 0;
  int _collectionCost = 0;
  int _evalCost = 0;

  /// STATS: Number of field watchers which are in use including child [WatchGroup]s.
  int get fieldCost => _fieldCost;
  int get totalFieldCost {
    var cost = _fieldCost;
    WatchGroup group = _watchGroupHead;
    while (group != null) {
      cost += group.totalFieldCost;
      group = group._nextWatchGroup;
    }
    return cost;
  }

  /// STATS: Number of collection watchers which are in use including child [WatchGroup]s.
  int get collectionCost => _collectionCost;
  int get totalCollectionCost {
    var cost = _collectionCost;
    WatchGroup group = _watchGroupHead;
    while (group != null) {
      cost += group.totalCollectionCost;
      group = group._nextWatchGroup;
    }
    return cost;
  }

  /// STATS: Number of invocation watchers (closures/methods) which are in use.
  int get evalCost => _evalCost;

  /// STATS: Number of invocation watchers which are in use including child [WatchGroup]s.
  int get totalEvalCost {
    var cost = _evalCost;
    WatchGroup group = _watchGroupHead;
    while (group != null) {
      cost += group.evalCost;
      group = group._nextWatchGroup;
    }
    return cost;
  }

  int _nextChildId = 0;
  _EvalWatchRecord _evalWatchHead, _evalWatchTail;
  /// Pointer for creating tree of [WatchGroup]s.
  WatchGroup _parentWatchGroup;
  WatchGroup _watchGroupHead, _watchGroupTail;
  WatchGroup _prevWatchGroup, _nextWatchGroup;

  WatchGroup._child(_parentWatchGroup, this._changeDetector, this.context,
                    this._cache, this._rootGroup)
      : _parentWatchGroup = _parentWatchGroup,
        id = '${_parentWatchGroup.id}.${_parentWatchGroup._nextChildId++}'
  {
    _marker.watchGrp = this;
    _evalWatchTail = _evalWatchHead = _marker;
  }

  WatchGroup._root(this._changeDetector, this.context)
      : id = '',
        _rootGroup = null,
        _parentWatchGroup = null,
        _cache = new Map<String, WatchRecord<_Handler>>()
  {
    _marker.watchGrp = this;
    _evalWatchTail = _evalWatchHead = _marker;
  }

  get isAttached {
    var group = this;
    var root = _rootGroup;
    while (group != null) {
      if (group == root){
        return true;
      }
      group = group._parentWatchGroup;
    }
    return false;
  }

  Watch watch(AST expression, ReactionFn reactionFn) {
    WatchRecord<_Handler> watchRecord =
        _cache.putIfAbsent(expression.expression,
            () => expression.setupWatch(this));
    return watchRecord.handler.addReactionFn(reactionFn);
  }

  /**
   * Watch a [name] field on [lhs] represented by [expression].
   *
   * - [name] the field to watch.
   * - [lhs] left-hand-side of the field.
   */
  WatchRecord<_Handler> addFieldWatch(AST lhs, String name, String expression) {
    var fieldHandler = new _FieldHandler(this, expression);

    // Create a Record for the current field and assign the change record
    // to the handler.
    var watchRecord = _changeDetector.watch(null, name, fieldHandler);
    _fieldCost++;
    fieldHandler.watchRecord = watchRecord;

    WatchRecord<_Handler> lhsWR = _cache.putIfAbsent(lhs.expression,
        () => lhs.setupWatch(this));

    // We set a field forwarding handler on LHS. This will allow the change
    // objects to propagate to the current WatchRecord.
    lhsWR.handler.addForwardHandler(fieldHandler);

    // propagate the value from the LHS to here
    fieldHandler.acceptValue(lhsWR.currentValue);
    return watchRecord;
  }

  WatchRecord<_Handler> addCollectionWatch(AST ast) {
    var collectionHandler = new _CollectionHandler(this, ast.expression);
    var watchRecord = _changeDetector.watch(null, null, collectionHandler);
    _collectionCost++;
    collectionHandler.watchRecord = watchRecord;
    WatchRecord<_Handler> astWR = _cache.putIfAbsent(ast.expression,
        () => ast.setupWatch(this));

    // We set a field forwarding handler on LHS. This will allow the change
    // objects to propagate to the current WatchRecord.
    astWR.handler.addForwardHandler(collectionHandler);

    // propagate the value from the LHS to here
    collectionHandler.acceptValue(astWR.currentValue);
    return watchRecord;
  }

  /**
   * Watch a [fn] function represented by an [expression].
   *
   * - [fn] function to evaluate.
   * - [argsAST] list of [AST]es which represent arguments passed to function.
   * - [expression] normalized expression used for caching.
   * - [isPure] A pure function is one which holds no internal state. This implies that the
   *   function is idempotent.
   */
  _EvalWatchRecord addFunctionWatch(Function fn, List<AST> argsAST,
                                    Map<Symbol, AST> namedArgsAST,
                                    String expression, bool isPure) =>
      _addEvalWatch(null, fn, null, argsAST, namedArgsAST, expression, isPure);

  /**
   * Watch a method [name]ed represented by an [expression].
   *
   * - [lhs] left-hand-side of the method.
   * - [name] name of the method.
   * - [argsAST] list of [AST]es which represent arguments passed to method.
   * - [expression] normalized expression used for caching.
   */
  _EvalWatchRecord addMethodWatch(AST lhs, String name, List<AST> argsAST,
                                  Map<Symbol, AST> namedArgsAST,
                                  String expression) =>
     _addEvalWatch(lhs, null, name, argsAST, namedArgsAST, expression, false);



  _EvalWatchRecord _addEvalWatch(AST lhsAST, Function fn, String name,
                                 List<AST> argsAST,
                                 Map<Symbol, AST> namedArgsAST,
                                 String expression, bool isPure) {
    _InvokeHandler invokeHandler = new _InvokeHandler(this, expression);
    var evalWatchRecord = new _EvalWatchRecord(
        _rootGroup._fieldGetterFactory, this, invokeHandler, fn, name,
        argsAST.length, isPure);
    invokeHandler.watchRecord = evalWatchRecord;

    if (lhsAST != null) {
      var lhsWR = _cache.putIfAbsent(lhsAST.expression,
          () => lhsAST.setupWatch(this));
      lhsWR.handler.addForwardHandler(invokeHandler);
      invokeHandler.acceptValue(lhsWR.currentValue);
    }

    // Convert the args from AST to WatchRecords
    for (var i = 0; i < argsAST.length; i++) {
      var ast = argsAST[i];
      WatchRecord<_Handler> record =
          _cache.putIfAbsent(ast.expression, () => ast.setupWatch(this));
      _ArgHandler handler = new _PositionalArgHandler(this, evalWatchRecord, i);
      _ArgHandlerList._add(invokeHandler, handler);
      record.handler.addForwardHandler(handler);
      handler.acceptValue(record.currentValue);
    }

    namedArgsAST.forEach((Symbol name, AST ast) {
      WatchRecord<_Handler> record = _cache.putIfAbsent(ast.expression,
          () => ast.setupWatch(this));
      _ArgHandler handler = new _NamedArgHandler(this, evalWatchRecord, name);
      _ArgHandlerList._add(invokeHandler, handler);
      record.handler.addForwardHandler(handler);
      handler.acceptValue(record.currentValue);
    });

    // Must be done last
    _EvalWatchList._add(this, evalWatchRecord);
    _evalCost++;
    if (_rootGroup.isInsideInvokeDirty) {
      // This check means that we are inside invoke reaction function.
      // Registering a new EvalWatch at this point will not run the
      // .check() on it which means it will not be processed, but its
      // reaction function will be run with null. So we process it manually.
      evalWatchRecord.check();
    }
    return evalWatchRecord;
  }

  WatchGroup get _childWatchGroupTail {
    var tail = this, nextTail;
    while ((nextTail = tail._watchGroupTail) != null) {
      tail = nextTail;
    }
    return tail;
  }

  /**
   * Create a new child [WatchGroup].
   *
   * - [context] if present the the child [WatchGroup] expressions will evaluate
   * against the new [context]. If not present than child expressions will
   * evaluate on same context allowing the reuse of the expression cache.
   */
  WatchGroup newGroup([Object context]) {
    _EvalWatchRecord prev = _childWatchGroupTail._evalWatchTail;
    _EvalWatchRecord next = prev._nextEvalWatch;
    var childGroup = new WatchGroup._child(
        this,
        _changeDetector.newGroup(),
        context == null ? this.context : context,
        <String, WatchRecord<_Handler>>{},
        _rootGroup == null ? this : _rootGroup);
    _WatchGroupList._add(this, childGroup);
    var marker = childGroup._marker;

    marker._prevEvalWatch = prev;
    marker._nextEvalWatch = next;
    prev._nextEvalWatch = marker;
    if (next != null) next._prevEvalWatch = marker;

    return childGroup;
  }

  /**
   * Remove/destroy [WatchGroup] and all of its [Watches].
   */
  void remove() {
    // TODO:(misko) This code is not right.
    // 1) It fails to release [ChangeDetector] [WatchRecord]s.

    _WatchGroupList._remove(_parentWatchGroup, this);
    _nextWatchGroup = _prevWatchGroup = null;
    _changeDetector.remove();
    _rootGroup._removeCount++;
    _parentWatchGroup = null;

    // Unlink the _watchRecord
    _EvalWatchRecord firstEvalWatch = _evalWatchHead;
    _EvalWatchRecord lastEvalWatch = _childWatchGroupTail._evalWatchTail;
    _EvalWatchRecord previous = firstEvalWatch._prevEvalWatch;
    _EvalWatchRecord next = lastEvalWatch._nextEvalWatch;
    if (previous != null) previous._nextEvalWatch = next;
    if (next != null) next._prevEvalWatch = previous;
    _evalWatchHead._prevEvalWatch = null;
    _evalWatchTail._nextEvalWatch = null;
    _evalWatchHead = _evalWatchTail = null;
  }

  toString() {
    var lines = [];
    if (this == _rootGroup) {
      var allWatches = [];
      var watch = _evalWatchHead;
      var prev = null;
      while (watch != null) {
        allWatches.add(watch.toString());
        assert(watch._prevEvalWatch == prev);
        prev = watch;
        watch = watch._nextEvalWatch;
      }
      lines.add('WATCHES: ${allWatches.join(', ')}');
    }

    var watches = [];
    var watch = _evalWatchHead;
    while (watch != _evalWatchTail) {
      watches.add(watch.toString());
      watch = watch._nextEvalWatch;
    }
    watches.add(watch.toString());

    lines.add('WatchGroup[$id](watches: ${watches.join(', ')})');
    var childGroup = _watchGroupHead;
    while (childGroup != null) {
      lines.add('  ' + childGroup.toString().replaceAll('\n', '\n  '));
      childGroup = childGroup._nextWatchGroup;
    }
    return lines.join('\n');
  }
}

/**
 * [RootWatchGroup]
 */
class RootWatchGroup extends WatchGroup {
  final FieldGetterFactory _fieldGetterFactory;
  Watch _dirtyWatchHead, _dirtyWatchTail;

  /**
   * Every time a [WatchGroup] is destroyed we increment the counter. During
   * [detectChanges] we reset the count. Before calling the reaction function,
   * we check [_removeCount] and if it is unchanged we can safely call the
   * reaction function. If it is changed we only call the reaction function
   * if the [WatchGroup] is still attached.
   */
  int _removeCount = 0;


  RootWatchGroup(this._fieldGetterFactory,
                 ChangeDetector changeDetector,
                 Object context)
      : super._root(changeDetector, context);

  RootWatchGroup get _rootGroup => this;

  /**
   * Detect changes and process the [ReactionFn]s.
   *
   * Algorithm:
   * 1) process the [ChangeDetector#collectChanges].
   * 2) process function/closure/method changes
   * 3) call an [ReactionFn]s
   *
   * Each step is called in sequence. ([ReactionFn]s are not called until all
   * previous steps are completed).
   */
  int detectChanges({ EvalExceptionHandler exceptionHandler,
                      ChangeLog changeLog,
                      AvgStopwatch fieldStopwatch,
                      AvgStopwatch evalStopwatch,
                      AvgStopwatch processStopwatch}) {
    // Process the Records from the change detector
    Iterator<Record<_Handler>> changedRecordIterator =
        (_changeDetector as ChangeDetector<_Handler>).collectChanges(
            exceptionHandler:exceptionHandler,
            stopwatch: fieldStopwatch);
    if (processStopwatch != null) processStopwatch.start();
    while (changedRecordIterator.moveNext()) {
      var record = changedRecordIterator.current;
      if (changeLog != null) changeLog(record.handler.expression,
                                       record.currentValue,
                                       record.previousValue);
      record.handler.onChange(record);
    }
    if (processStopwatch != null) processStopwatch.stop();

    if (evalStopwatch != null) evalStopwatch.start();
    // Process our own function evaluations
    _EvalWatchRecord evalRecord = _evalWatchHead;
    int evalCount = 0;
    while (evalRecord != null) {
      try {
        if (evalStopwatch != null) evalCount++;
        if (evalRecord.check() && changeLog != null) {
          changeLog(evalRecord.handler.expression,
                    evalRecord.currentValue,
                    evalRecord.previousValue);
        }
      } catch (e, s) {
        if (exceptionHandler == null) rethrow; else exceptionHandler(e, s);
      }
      evalRecord = evalRecord._nextEvalWatch;
    }
    if (evalStopwatch != null) evalStopwatch..stop()..increment(evalCount);

    // Because the handler can forward changes between each other synchronously
    // We need to call reaction functions asynchronously. This processes the
    // asynchronous reaction function queue.
    int count = 0;
    if (processStopwatch != null) processStopwatch.start();
    Watch dirtyWatch = _dirtyWatchHead;
    _dirtyWatchHead = null;
    RootWatchGroup root = _rootGroup;
    try {
      while (dirtyWatch != null) {
        count++;
        try {
          if (root._removeCount == 0 || dirtyWatch._watchGroup.isAttached) {
            dirtyWatch.invoke();
          }
        } catch (e, s) {
          if (exceptionHandler == null) rethrow; else exceptionHandler(e, s);
        }
        var nextDirtyWatch = dirtyWatch._nextDirtyWatch;
        dirtyWatch._nextDirtyWatch = null;
        dirtyWatch = nextDirtyWatch;
      }
    } finally {
      _dirtyWatchTail = null;
      root._removeCount = 0;
    }
    if (processStopwatch != null) processStopwatch..stop()..increment(count);
    return count;
  }

  bool get isInsideInvokeDirty =>
      _dirtyWatchHead == null && _dirtyWatchTail != null;

  /**
   * Add Watch into the asynchronous queue for later processing.
   */
  Watch _addDirtyWatch(Watch watch) {
    if (!watch._dirty) {
      watch._dirty = true;
      if (_dirtyWatchTail == null) {
        _dirtyWatchHead = _dirtyWatchTail = watch;
      } else {
        _dirtyWatchTail._nextDirtyWatch = watch;
        _dirtyWatchTail = watch;
      }
      watch._nextDirtyWatch = null;
    }
    return watch;
  }
}

/**
 * [Watch] corresponds to an individual [watch] registration on the watchGrp.
 */
class Watch {
  Watch _previousWatch, _nextWatch;

  final Record<_Handler> _record;
  final ReactionFn reactionFn;
  final WatchGroup _watchGroup;

  bool _dirty = false;
  bool _deleted = false;
  Watch _nextDirtyWatch;

  Watch(this._watchGroup, this._record, this.reactionFn);

  get expression => _record.handler.expression;
  void invoke() {
    if (_deleted || !_dirty) return;
    _dirty = false;
    reactionFn(_record.currentValue, _record.previousValue);
  }

  void remove() {
    if (_deleted) throw new StateError('Already deleted!');
    _deleted = true;
    var handler = _record.handler;
    _WatchList._remove(handler, this);
    handler.release();
  }
}

/**
 * This class processes changes from the change detector. The changes are
 * forwarded onto the next [_Handler] or queued up in case of reaction function.
 *
 * Given these two expression: 'a.b.c' => rfn1 and 'a.b' => rfn2
 * The resulting data structure is:
 *
 * _Handler             +--> _Handler             +--> _Handler
 *   - delegateHandler -+      - delegateHandler -+      - delegateHandler = null
 *   - expression: 'a'         - expression: 'a.b'       - expression: 'a.b.c'
 *   - watchObject: context    - watchObject: context.a  - watchObject: context.a.b
 *   - watchRecord: 'a'        - watchRecord 'b'         - watchRecord 'c'
 *   - reactionFn: null        - reactionFn: rfn1        - reactionFn: rfn2
 *
 * Notice how the [_Handler]s coalesce their watching. Also notice that any
 * changes detected at one handler are propagated to the next handler.
 */
abstract class _Handler implements _LinkedList, _LinkedListItem, _WatchList {
  // Used for forwarding changes to delegates
  _Handler _head, _tail;
  _Handler _next, _previous;
  Watch _watchHead, _watchTail;

  final String expression;
  final WatchGroup watchGrp;

  WatchRecord<_Handler> watchRecord;
  _Handler forwardingHandler;

  _Handler(this.watchGrp, this.expression) {
    assert(watchGrp != null);
    assert(expression != null);
  }

  Watch addReactionFn(ReactionFn reactionFn) {
    assert(_next != this); // verify we are not detached
    return watchGrp._rootGroup._addDirtyWatch(_WatchList._add(this,
        new Watch(watchGrp, watchRecord, reactionFn)));
  }

  void addForwardHandler(_Handler forwardToHandler) {
    assert(forwardToHandler.forwardingHandler == null);
    _LinkedList._add(this, forwardToHandler);
    forwardToHandler.forwardingHandler = this;
  }

  /// Return true if release has happened
  bool release() {
    if (_WatchList._isEmpty(this) && _LinkedList._isEmpty(this)) {
      _releaseWatch();
      // Remove ourselves from cache, or else new registrations will go to us,
      // but we are dead
      watchGrp._cache.remove(expression);

      if (forwardingHandler != null) {
        // TODO(misko): why do we need this check?
        _LinkedList._remove(forwardingHandler, this);
        forwardingHandler.release();
      }

      // We can remove ourselves
      assert((_next = _previous = this) == this); // mark ourselves as detached
      return true;
    } else {
      return false;
    }
  }

  void _releaseWatch() {
    watchRecord.remove();
    watchGrp._fieldCost--;
  }
  acceptValue(object) => null;

  void onChange(Record<_Handler> record) {
    assert(_next != this); // verify we are not detached
    // If we have reaction functions than queue them up for asynchronous
    // processing.
    Watch watch = _watchHead;
    while (watch != null) {
      watchGrp._rootGroup._addDirtyWatch(watch);
      watch = watch._nextWatch;
    }
    // If we have a delegateHandler then forward the new value to it.
    _Handler delegateHandler = _head;
    while (delegateHandler != null) {
      delegateHandler.acceptValue(record.currentValue);
      delegateHandler = delegateHandler._next;
    }
  }
}

class _ConstantHandler extends _Handler {
  _ConstantHandler(WatchGroup watchGroup, String expression, constantValue)
      : super(watchGroup, expression)
  {
    watchRecord = new _EvalWatchRecord.constant(this, constantValue);
  }
  release() => null;
}

class _FieldHandler extends _Handler {
  _FieldHandler(watchGrp, expression): super(watchGrp, expression);

  /**
   * This function forwards the watched object to the next [_Handler]
   * synchronously.
   */
  void acceptValue(object) {
    watchRecord.object = object;
    if (watchRecord.check()) onChange(watchRecord);
  }
}

class _CollectionHandler extends _Handler {
  _CollectionHandler(WatchGroup watchGrp, String expression)
      : super(watchGrp, expression);
  /**
   * This function forwards the watched object to the next [_Handler] synchronously.
   */
  void acceptValue(object) {
    watchRecord.object = object;
    if (watchRecord.check()) onChange(watchRecord);
  }

  void _releaseWatch() {
    watchRecord.remove();
    watchGrp._collectionCost--;
  }
}

abstract class _ArgHandler extends _Handler {
  _ArgHandler _previousArgHandler, _nextArgHandler;

  // TODO(misko): Why do we override parent?
  final _EvalWatchRecord watchRecord;
  _ArgHandler(WatchGroup watchGrp, String expression, this.watchRecord)
      : super(watchGrp, expression);

  _releaseWatch() => null;
}

class _PositionalArgHandler extends _ArgHandler {
  final int index;
  _PositionalArgHandler(WatchGroup watchGrp, _EvalWatchRecord record, int index)
      : this.index = index,
        super(watchGrp, 'arg[$index]', record);

  void acceptValue(object) {
    watchRecord.dirtyArgs = true;
    watchRecord.args[index] = object;
  }
}

class _NamedArgHandler extends _ArgHandler {
  final Symbol name;

  _NamedArgHandler(WatchGroup watchGrp, _EvalWatchRecord record, Symbol name)
      : this.name = name,
        super(watchGrp, 'namedArg[$name]', record);

  void acceptValue(object) {
    watchRecord.dirtyArgs = true;
    watchRecord.namedArgs[name] = object;
  }
}

class _InvokeHandler extends _Handler implements _ArgHandlerList {
  _ArgHandler _argHandlerHead, _argHandlerTail;

  _InvokeHandler(WatchGroup watchGrp, String expression)
      : super(watchGrp, expression);

  void acceptValue(object) {
    watchRecord.object = object;
  }

  void _releaseWatch() {
    (watchRecord as _EvalWatchRecord).remove();
  }

  bool release() {
    if (super.release()) {
      _ArgHandler current = _argHandlerHead;
      while (current != null) {
        current.release();
        current = current._nextArgHandler;
      }
      return true;
    } else {
      return false;
    }
  }
}


class _EvalWatchRecord implements WatchRecord<_Handler> {
  static const int _MODE_INVALID_                  = -2;
  static const int _MODE_DELETED_                  = -1;
  static const int _MODE_MARKER_                   = 0;
  static const int _MODE_PURE_FUNCTION_            = 1;
  static const int _MODE_FUNCTION_                 = 2;
  static const int _MODE_PURE_FUNCTION_APPLY_      = 3;
  static const int _MODE_NULL_                     = 4;
  static const int _MODE_FIELD_OR_METHOD_CLOSURE_  = 5;
  static const int _MODE_METHOD_                   = 6;
  static const int _MODE_FIELD_CLOSURE_            = 7;
  static const int _MODE_MAP_CLOSURE_              = 8;
  WatchGroup watchGrp;
  final _Handler handler;
  final List args;
  final Map<Symbol, dynamic> namedArgs =  new Map<Symbol, dynamic>();
  final String name;
  int mode;
  Function fn;
  FieldGetterFactory _fieldGetterFactory;
  bool dirtyArgs = true;

  dynamic currentValue, previousValue, _object;
  _EvalWatchRecord _prevEvalWatch, _nextEvalWatch;

  _EvalWatchRecord(this._fieldGetterFactory, this.watchGrp, this.handler,
                   this.fn, this.name, int arity, bool pure)
      : args = new List(arity)
  {
    if (fn is FunctionApply) {
      mode = pure ? _MODE_PURE_FUNCTION_APPLY_: _MODE_INVALID_;
    } else if (fn is Function) {
      mode = pure ? _MODE_PURE_FUNCTION_ : _MODE_FUNCTION_;
    } else {
      mode = _MODE_NULL_;
    }
  }

  _EvalWatchRecord.marker()
      : mode = _MODE_MARKER_,
        _fieldGetterFactory = null,
        watchGrp = null,
        handler = null,
        args = null,
        fn = null,
        name = null;

  _EvalWatchRecord.constant(_Handler handler, dynamic constantValue)
      : mode = _MODE_MARKER_,
        _fieldGetterFactory = null,
        handler = handler,
        currentValue = constantValue,
        watchGrp = null,
        args = null,
        fn = null,
        name = null;

  get field => '()';

  get object => _object;

  set object(value) {
    assert(mode != _MODE_DELETED_);
    assert(mode != _MODE_MARKER_);
    assert(mode != _MODE_FUNCTION_);
    assert(mode != _MODE_PURE_FUNCTION_);
    assert(mode != _MODE_PURE_FUNCTION_APPLY_);
    _object = value;

    if (value == null) {
      mode = _MODE_NULL_;
    } else {
      if (value is Map) {
        mode =  _MODE_MAP_CLOSURE_;
      } else {
        mode = _MODE_FIELD_OR_METHOD_CLOSURE_;
        fn = _fieldGetterFactory.getter(value, name);
      }
    }
  }

  bool check() {
    var value;
    switch (mode) {
      case _MODE_MARKER_:
      case _MODE_NULL_:
        return false;
      case _MODE_PURE_FUNCTION_:
        if (!dirtyArgs) return false;
        value = Function.apply(fn, args, namedArgs);
        dirtyArgs = false;
        break;
      case _MODE_FUNCTION_:
        value = Function.apply(fn, args, namedArgs);
        dirtyArgs = false;
        break;
      case _MODE_PURE_FUNCTION_APPLY_:
        if (!dirtyArgs) return false;
        value = (fn as FunctionApply).apply(args);
        dirtyArgs = false;
        break;
      case _MODE_FIELD_OR_METHOD_CLOSURE_:
        var closure = fn(_object);
        // NOTE: When Dart looks up a method "foo" on object "x", it returns a
        // new closure for each lookup.  They compare equal via "==" but are no
        // identical().  There's no point getting a new value each time and
        // decide it's the same so we'll skip further checking after the first
        // time.
        if (closure is Function && !identical(closure, fn(_object))) {
          fn = closure;
          mode = _MODE_METHOD_;
        } else {
          mode = _MODE_FIELD_CLOSURE_;
        }
        value = (closure == null) ? null : Function.apply(closure, args, namedArgs);
        break;
      case _MODE_METHOD_:
        value = Function.apply(fn, args, namedArgs);
        break;
      case _MODE_FIELD_CLOSURE_:
        var closure = fn(_object);
        value = (closure == null) ? null : Function.apply(closure, args, namedArgs);
        break;
      case _MODE_MAP_CLOSURE_:
        var closure = object[name];
        value = (closure == null) ? null : Function.apply(closure, args, namedArgs);
        break;
      default:
        assert(false);
    }

    var current = currentValue;
    if (!identical(current, value)) {
      if (value is String && current is String && value == current) {
        // it is really the same, recover and save so next time identity is same
        current = value;
      } else {
        previousValue = current;
        currentValue = value;
        handler.onChange(this);
        return true;
      }
    }
    return false;
  }

  get nextChange => null;

  void remove() {
    assert(mode != _MODE_DELETED_);
    assert((mode = _MODE_DELETED_) == _MODE_DELETED_); // Mark as deleted.
    watchGrp._evalCost--;
    _EvalWatchList._remove(watchGrp, this);
  }

  String toString() {
    if (mode == _MODE_MARKER_) return 'MARKER[$currentValue]';
    return '${watchGrp.id}:${handler.expression}';
  }
}
