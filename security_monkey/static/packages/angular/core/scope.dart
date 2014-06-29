part of angular.core_internal;

typedef EvalFunction0();
typedef EvalFunction1(context);

/**
 * Injected into the listener function within [Scope.on] to provide
 * event-specific details to the scope listener.
 */
class ScopeEvent {
  static final String DESTROY = 'ng-destroy';

  /**
   * Data attached to the event. This would be the optional parameter
   * from [Scope.emit] and [Scope.broadcast].
   */
  final data;

  /**
   * The name of the intercepted scope event.
   */
  final String name;

  /**
   * The origin scope that triggered the event (via broadcast or emit).
   */
  final Scope targetScope;

  /**
   * The destination scope that intercepted the event. As
   * the event traverses the scope hierarchy the the event instance
   * stays the same, but the [currentScope] reflects the scope
   * of the current listener which is firing.
   */
  Scope get currentScope => _currentScope;
  Scope _currentScope;

  /**
   * true or false depending on if [stopPropagation] was executed.
   */
  bool get propagationStopped => _propagationStopped;
  bool _propagationStopped = false;

  /**
   * true or false depending on if [preventDefault] was executed.
   */
  bool get defaultPrevented => _defaultPrevented;
  bool _defaultPrevented = false;

  /**
   * [name] - The name of the scope event.
   * [targetScope] - The destination scope that is listening on the event.
   */
  ScopeEvent(this.name, this.targetScope, this.data);

  /**
   * Prevents the intercepted event from propagating further to successive
   * scopes.
   */
  void stopPropagation () {
    _propagationStopped = true;
  }

  /**
   * Sets the defaultPrevented flag to true.
   */
  void preventDefault() {
    _defaultPrevented = true;
  }
}

/**
 * Allows the configuration of [Scope.digest] iteration maximum time-to-live
 * value. Digest keeps checking the state of the watcher getters until it
 * can execute one full iteration with no watchers triggering. TTL is used
 * to prevent an infinite loop where watch A triggers watch B which in turn
 * triggers watch A. If the system does not stabilize in TTL iterations then
 * the digest is stopped and an exception is thrown.
 */
@Injectable()
class ScopeDigestTTL {
  final int ttl;
  ScopeDigestTTL(): ttl = 5;
  ScopeDigestTTL.value(this.ttl);
}

//TODO(misko): I don't think this should be in scope.
class ScopeLocals implements Map {
  static wrapper(scope, Map<String, Object> locals) =>
      new ScopeLocals(scope, locals);

  Map _scope;
  Map<String, Object> _locals;

  ScopeLocals(this._scope, this._locals);

  void operator []=(String name, value) {
    _scope[name] = value;
  }
  dynamic operator [](String name) {
    // Map needed to clear Dart2js warning
    Map map = _locals.containsKey(name) ? _locals : _scope;
    return map[name];
  }

  bool get isEmpty => _scope.isEmpty && _locals.isEmpty;
  bool get isNotEmpty => _scope.isNotEmpty || _locals.isNotEmpty;
  List<String> get keys => _scope.keys;
  List get values => _scope.values;
  int get length => _scope.length;

  void forEach(fn) {
    _scope.forEach(fn);
  }
  dynamic remove(key) => _scope.remove(key);
  void clear() {
    _scope.clear;
  }
  bool containsKey(key) => _scope.containsKey(key);
  bool containsValue(key) => _scope.containsValue(key);
  void addAll(map) {
    _scope.addAll(map);
  }
  dynamic putIfAbsent(key, fn) => _scope.putIfAbsent(key, fn);
}

/**
 * [Scope] is represents a collection of [watch]es [observe]ers, and [context]
 * for the watchers, observers and [eval]uations. Scopes structure loosely
 * mimics the DOM structure. Scopes and [View]s are bound to each other.
 * As scopes are created and destroyed by [ViewFactory] they are responsible
 * for change detection, change processing and memory management.
 */
class Scope {
  final String id;
  int _childScopeNextId = 0;

  /**
   * The default execution context for [watch]es [observe]ers, and [eval]uation.
   */
  final context;

  /**
   * The [RootScope] of the application.
   */
  final RootScope rootScope;

  Scope _parentScope;

  /**
   * The parent [Scope].
   */
  Scope get parentScope => _parentScope;

  final ScopeStats _stats;

  /**
   * Return `true` if the scope has been destroyed. Once scope is destroyed
   * No operations are allowed on it.
   */
  bool get isDestroyed {
    var scope = this;
    while (scope != null) {
      if (scope == rootScope) return false;
      scope = scope._parentScope;
    }
    return true;
  }

  /**
   * Returns true if the scope is still attached to the [RootScope].
   */
  bool get isAttached => !isDestroyed;

  // TODO(misko): WatchGroup should be private.
  // Instead we should expose performance stats about the watches
  // such as # of watches, checks/1ms, field checks, function checks, etc
  final WatchGroup _readWriteGroup;
  final WatchGroup _readOnlyGroup;

  Scope _childHead, _childTail, _next, _prev;
  _Streams _streams;

  /// Do not use. Exposes internal state for testing.
  bool get hasOwnStreams => _streams != null  && _streams._scope == this;

  Scope(Object this.context, this.rootScope, this._parentScope,
        this._readWriteGroup, this._readOnlyGroup, this.id,
        this._stats);

  /**
   * Use [watch] to set up change detection on an expression.
   *
   * * [expression]: The expression to watch for changes.
   *   Expressions may use a special notation in addition to what is supported by the parser.
   *   In particular:
   *   - If an expression begins with '::', it is unwatched as soon as it evaluates to a non-null
   *   value.
   *   - If an expression begins with ':', it only calls the [reactionFn] if the expression
   *   evaluates to a non-null value.
   * * [reactionFn]: The reaction function to execute when a change is detected in the watched
   *   expression.
   * * [context]: The object against which the expression is evaluated. This defaults to the
   *   [Scope.context] if no context is specified.
   * * [formatters]: If the watched expression contains formatters,
   *   this map specifies the set of formatters that are used by the expression.
   * * [canChangeModel]: Specifies whether the [reactionFn] changes the model. Reaction
   *   functions that change the model are processed as part of the [digest] cycle. Otherwise,
   *   they are processed as part of the [flush] cycle.
   * * [collection]: If [:true:], then the expression points to a collection (a list or a map),
   *   and the collection should be shallow watched. If [:false:] then the expression is watched
   *   by reference. When watching a collection, the reaction function receives a
   *   [CollectionChangeItem] that lists all the changes.
   */
  Watch watch(String expression, ReactionFn reactionFn,  {context,
      FormatterMap formatters, bool canChangeModel: true, bool collection: false}) {
    assert(isAttached);
    assert(expression is String);
    assert(canChangeModel is bool);

    Watch watch;
    ReactionFn fn = reactionFn;
    if (expression.isEmpty) {
      expression = '""';
    } else {
      if (expression.startsWith('::')) {
        expression = expression.substring(2);
        fn = (value, last) {
          if (value != null) {
            watch.remove();
            return reactionFn(value, last);
          }
        };
      } else if (expression.startsWith(':')) {
        expression = expression.substring(1);
        fn = (value, last) {
          if (value != null)  reactionFn(value, last);
        };
      }
    }

    AST ast = rootScope._astParser(expression, context: context,
        formatters: formatters, collection: collection);

    WatchGroup group = canChangeModel ? _readWriteGroup : _readOnlyGroup;
    return watch = group.watch(ast, fn);
  }

  dynamic eval(expression, [Map locals]) {
    assert(isAttached);
    assert(expression == null ||
           expression is String ||
           expression is Function);
    if (expression is String && expression.isNotEmpty) {
      var obj = locals == null ? context : new ScopeLocals(context, locals);
      return rootScope._parser(expression).eval(obj);
    }

    assert(locals == null);
    if (expression is EvalFunction1) return expression(context);
    if (expression is EvalFunction0) return expression();
    return null;
  }

  dynamic apply([expression, Map locals]) {
    _assertInternalStateConsistency();
    rootScope._transitionState(null, RootScope.STATE_APPLY);
    try {
      return eval(expression, locals);
    } catch (e, s) {
      rootScope._exceptionHandler(e, s);
    } finally {
      rootScope.._transitionState(RootScope.STATE_APPLY, null)
               ..digest()
               ..flush();
    }
  }

  ScopeEvent emit(String name, [data]) {
    assert(isAttached);
    return _Streams.emit(this, name, data);
  }

  ScopeEvent broadcast(String name, [data]) {
    assert(isAttached);
    return _Streams.broadcast(this, name, data);
  }

  ScopeStream on(String name) {
    assert(isAttached);
    return _Streams.on(this, rootScope._exceptionHandler, name);
  }

  Scope createChild(Object childContext) {
    assert(isAttached);
    var child = new Scope(childContext, rootScope, this,
                          _readWriteGroup.newGroup(childContext),
                          _readOnlyGroup.newGroup(childContext),
                         '$id:${_childScopeNextId++}',
                         _stats);

    var prev = _childTail;
    child._prev = prev;
    if (prev == null) _childHead = child; else prev._next = child;
    _childTail = child;
    return child;
  }

  void destroy() {
    assert(isAttached);
    broadcast(ScopeEvent.DESTROY);
    _Streams.destroy(this);

    if (_prev == null) {
      _parentScope._childHead = _next;
    } else {
      _prev._next = _next;
    }
    if (_next == null) {
      _parentScope._childTail = _prev;
    } else {
      _next._prev = _prev;
    }

    _next = _prev = null;

    _readWriteGroup.remove();
    _readOnlyGroup.remove();
    _parentScope = null;
  }

  _assertInternalStateConsistency() {
    assert((() {
      rootScope._verifyStreams(null, '', []);
      return true;
    })());
  }

  Map<bool,int> _verifyStreams(parentScope, prefix, log) {
    assert(_parentScope == parentScope);
    var counts = {};
    var typeCounts = _streams == null ? {} : _streams._typeCounts;
    var connection = _streams != null && _streams._scope == this ? '=' : '-';
    log..add(prefix)..add(hashCode)..add(connection)..add(typeCounts)..add('\n');
    if (_streams == null) {
    } else if (_streams._scope == this) {
      _streams._streams.forEach((k, ScopeStream stream){
        if (stream.subscriptions.isNotEmpty) {
          counts[k] = 1 + (counts.containsKey(k) ? counts[k] : 0);
        }
      });
    }
    var childScope = _childHead;
    while (childScope != null) {
      childScope._verifyStreams(this, '  $prefix', log).forEach((k, v) {
        counts[k] = v + (counts.containsKey(k) ? counts[k] : 0);
      });
      childScope = childScope._next;
    }
    if (!_mapEqual(counts, typeCounts)) {
      throw 'Streams actual: $counts != bookkeeping: $typeCounts\n'
            'Offending scope: [scope: ${this.hashCode}]\n'
            '${log.join('')}';
    }
    return counts;
  }
}

_mapEqual(Map a, Map b) => a.length == b.length &&
    a.keys.every((k) => b.containsKey(k) && a[k] == b[k]);

/**
 * ScopeStats collects and emits statistics about a [Scope].
 *
 * ScopeStats supports emitting the results. Result emission can be started or
 * stopped at runtime. The result emission can is configured by supplying a
 * [ScopeStatsEmitter].
 */
@Injectable()
class ScopeStats {
  final fieldStopwatch = new AvgStopwatch();
  final evalStopwatch = new AvgStopwatch();
  final processStopwatch = new AvgStopwatch();

  List<int> _digestLoopTimes = [];
  int _flushPhaseDuration = 0 ;
  int _assertFlushPhaseDuration = 0;

  int _loopNo = 0;
  ScopeStatsEmitter _emitter;
  ScopeStatsConfig _config;

  /**
   * Construct a new instance of ScopeStats.
   */
  ScopeStats(this._emitter, this._config);

  void digestStart() {
    _digestLoopTimes = [];
    _stopwatchReset();
    _loopNo = 0;
  }

  int _allStagesDuration() {
    return fieldStopwatch.elapsedMicroseconds +
      evalStopwatch.elapsedMicroseconds +
      processStopwatch.elapsedMicroseconds;
  }

  _stopwatchReset() {
    fieldStopwatch.reset();
    evalStopwatch.reset();
    processStopwatch.reset();
  }

  void digestLoop(int changeCount) {
    _loopNo++;
    if (_config.emit && _emitter != null) {
      _emitter.emit(_loopNo.toString(), fieldStopwatch, evalStopwatch,
        processStopwatch);
    }
    _digestLoopTimes.add( _allStagesDuration() );
    _stopwatchReset();
  }

  void digestEnd() {
  }

  void domWriteStart() {}
  void domWriteEnd() {}
  void domReadStart() {}
  void domReadEnd() {}
  void flushStart() {
    _stopwatchReset();
  }
  void flushEnd() {
    if (_config.emit && _emitter != null) {
      _emitter.emit(RootScope.STATE_FLUSH, fieldStopwatch, evalStopwatch,
        processStopwatch);
    }
    _flushPhaseDuration = _allStagesDuration();
  }
  void flushAssertStart() {
    _stopwatchReset();
  }
  void flushAssertEnd() {
    if (_config.emit && _emitter != null) {
      _emitter.emit(RootScope.STATE_FLUSH_ASSERT, fieldStopwatch, evalStopwatch,
        processStopwatch);
    }
    _assertFlushPhaseDuration = _allStagesDuration();
  }

  void cycleEnd() {
  }
}

/**
 * ScopeStatsEmitter is in charge of formatting the [ScopeStats] and outputting
 * a message.
 */
@Injectable()
class ScopeStatsEmitter {
  static String _PAD_ = '                       ';
  static String _HEADER_ = pad('APPLY', 7) + ':'+
        pad('FIELD',    19) + pad('|', 20) +
        pad('EVAL',     19) + pad('|', 20) +
        pad('REACTION', 19) + pad('|', 20) +
        pad('TOTAL',    10) + '\n';
  final _nfDec = new NumberFormat("0.00", "en_US");
  final _nfInt = new NumberFormat("0", "en_US");

  static pad(String str, int size) => _PAD_.substring(0, max(size - str.length, 0)) + str;

  _ms(num value) => '${pad(_nfDec.format(value), 9)} ms';
  _us(num value) => _ms(value / 1000);
  _tally(num value) => '${pad(_nfInt.format(value), 6)}';

  /**
   * Emit a message based on the phase and state of stopwatches.
   */
  void emit(String phaseOrLoopNo, AvgStopwatch fieldStopwatch,
            AvgStopwatch evalStopwatch, AvgStopwatch processStopwatch) {
    var total = fieldStopwatch.elapsedMicroseconds +
                evalStopwatch.elapsedMicroseconds +
                processStopwatch.elapsedMicroseconds;
    print('${_formatPrefix(phaseOrLoopNo)} '
          '${_stat(fieldStopwatch)} | '
          '${_stat(evalStopwatch)} | '
          '${_stat(processStopwatch)} | '
          '${_ms(total/1000)}');
  }

  String _formatPrefix(String prefix) {
    if (prefix == RootScope.STATE_FLUSH) return '  flush:';
    if (prefix == RootScope.STATE_FLUSH_ASSERT) return ' assert:';

    return (prefix == '1' ? _HEADER_ : '')  + '     #$prefix:';
  }

  String _stat(AvgStopwatch s) {
    return '${_tally(s.count)} / ${_us(s.elapsedMicroseconds)} @(${_tally(s.ratePerMs)} #/ms)';
  }
}

/**
 * ScopeStatsConfig is used to modify behavior of [ScopeStats]. You can use this
 * object to modify behavior at runtime too.
 */
class ScopeStatsConfig {
  var emit = false;

  ScopeStatsConfig();
  ScopeStatsConfig.enabled() {
    emit = true;
  }
}
/**
 *
 * Every Angular application has exactly one RootScope. RootScope extends Scope, adding
 * services related to change detection, async unit-of-work processing, and DOM read/write queues.
 * The RootScope can not be destroyed.
 *
 * ## Lifecycle
 *
 * All work in Angular must be done within a context of a VmTurnZone. VmTurnZone detects the end
 * of the VM turn, and calls the Apply method to process the changes at the end of VM turn.
 *
 */
@Injectable()
class RootScope extends Scope {
  static final STATE_APPLY = 'apply';
  static final STATE_DIGEST = 'digest';
  static final STATE_FLUSH = 'flush';
  static final STATE_FLUSH_ASSERT = 'assert';

  final ExceptionHandler _exceptionHandler;
  final _AstParser _astParser;
  final Parser _parser;
  final ScopeDigestTTL _ttl;
  final VmTurnZone _zone;

  _FunctionChain _runAsyncHead, _runAsyncTail;
  _FunctionChain _domWriteHead, _domWriteTail;
  _FunctionChain _domReadHead, _domReadTail;

  final ScopeStats _scopeStats;

  String _state;

  /**
   *
   * While processing data bindings, Angular passes through multiple states. When testing or
   * debugging, it can be useful to access the current `state`, which is one of the following:
   *
   * * null
   * * apply
   * * digest
   * * flush
   * * assert
   *
   * ##null
   *
   *  Angular is not currently processing changes
   *
   * ##apply
   *
   * The apply state begins by executing the optional expression within the context of
   * angular change detection mechanism. Any exceptions are delegated to [ExceptionHandler]. At the
   * end of apply state RootScope enters the digest followed by flush phase (optionally if asserts
   * enabled run assert phase.)
   *
   * ##digest
   *
   * The apply state begins by processing the async queue,
   * followed by change detection
   * on non-DOM listeners. Any changes detected are process using the reaction function. The digest
   * phase is repeated as long as at least one change has been detected. By default, after 5
   * iterations the model is considered unstable and angular exists with an exception. (See
   * ScopeDigestTTL)
   *
   * ##flush
   *
   * The flush phase consists of these steps:
   *
   * 1. processing the DOM write queue
   * 2. change detection on DOM only updates (these are reaction functions which must
   *    not change the model state and hence don't need stabilization as in digest phase).
   * 3. processing the DOM read queue
   * 4. repeat steps 1 and 3 (not 2) until queues are empty
   *
   * ##assert
   *
   * Optionally if Dart assert is on, verify that flush reaction functions did not make any changes
   * to model and throw error if changes detected.
   *
   */
  String get state => _state;

  RootScope(Object context, Parser parser, FieldGetterFactory fieldGetterFactory,
            FormatterMap formatters, this._exceptionHandler, this._ttl, this._zone,
            ScopeStats _scopeStats, ClosureMap closureMap)
      : _scopeStats = _scopeStats,
        _parser = parser,
        _astParser = new _AstParser(parser, closureMap),
        super(context, null, null,
            new RootWatchGroup(fieldGetterFactory,
                new DirtyCheckingChangeDetector(fieldGetterFactory), context),
            new RootWatchGroup(fieldGetterFactory,
                new DirtyCheckingChangeDetector(fieldGetterFactory), context),
            '',
            _scopeStats)
  {
    _zone.onTurnDone = apply;
    _zone.onError = (e, s, ls) => _exceptionHandler(e, s);
  }

  RootScope get rootScope => this;
  bool get isAttached => true;

/**
  * Propagates changes between different parts of the application model. Normally called by
  * [VMTurnZone] right before DOM rendering to initiate data binding. May also be called directly
  * for unit testing.
  *
  * Before each iteration of change detection, [digest] first processes the async queue. Any
  * work scheduled on the queue is executed before change detection. Since work scheduled on
  * the queue may generate more async calls, [digest] must process the queue multiple times before
  * it completes. The async queue must be empty before the model is considered stable.
  *
  * Next, [digest] collects the changes that have occurred in the model. For each change,
  * [digest] calls the associated [ReactionFn]. Since a [ReactionFn] may further change the model,
  * [digest] processes changes multiple times until no more changes are detected.
  *
  * If the model does not stabilize within 5 iterations, an exception is thrown. See
  * [ScopeDigestTTL].
  */
  void digest() {
    _transitionState(null, STATE_DIGEST);
    try {
      var rootWatchGroup = _readWriteGroup as RootWatchGroup;

      int digestTTL = _ttl.ttl;
      const int LOG_COUNT = 3;
      List log;
      List digestLog;
      var count;
      ChangeLog changeLog;
      _scopeStats.digestStart();
      do {
        while (_runAsyncHead != null) {
          try {
            _runAsyncHead.fn();
          } catch (e, s) {
            _exceptionHandler(e, s);
          }
          _runAsyncHead = _runAsyncHead._next;
        }
        _runAsyncTail = null;

        digestTTL--;
        count = rootWatchGroup.detectChanges(
            exceptionHandler: _exceptionHandler,
            changeLog: changeLog,
            fieldStopwatch: _scopeStats.fieldStopwatch,
            evalStopwatch: _scopeStats.evalStopwatch,
            processStopwatch: _scopeStats.processStopwatch);

        if (digestTTL <= LOG_COUNT) {
          if (changeLog == null) {
            log = [];
            digestLog = [];
            changeLog = (e, c, p) => digestLog.add('$e: $c <= $p');
          } else {
            log.add(digestLog.join(', '));
            digestLog.clear();
          }
        }
        if (digestTTL == 0) {
          throw 'Model did not stabilize in ${_ttl.ttl} digests. '
                'Last $LOG_COUNT iterations:\n${log.join('\n')}';
        }
        _scopeStats.digestLoop(count);
      } while (count > 0);
    } finally {
      _scopeStats.digestEnd();
      _transitionState(STATE_DIGEST, null);
    }
  }

  void flush() {
    _stats.flushStart();
    _transitionState(null, STATE_FLUSH);
    RootWatchGroup readOnlyGroup = this._readOnlyGroup as RootWatchGroup;
    bool runObservers = true;
    try {
      do {
        if (_domWriteHead != null) _stats.domWriteStart();
        while (_domWriteHead != null) {
          try {
            _domWriteHead.fn();
          } catch (e, s) {
            _exceptionHandler(e, s);
          }
          _domWriteHead = _domWriteHead._next;
          if (_domWriteHead == null) _stats.domWriteEnd();
        }
        _domWriteTail = null;
        if (runObservers) {
          runObservers = false;
          readOnlyGroup.detectChanges(exceptionHandler:_exceptionHandler,
              fieldStopwatch: _scopeStats.fieldStopwatch,
              evalStopwatch: _scopeStats.evalStopwatch,
              processStopwatch: _scopeStats.processStopwatch);
        }
        if (_domReadHead != null) _stats.domReadStart();
        while (_domReadHead != null) {
          try {
            _domReadHead.fn();
          } catch (e, s) {
            _exceptionHandler(e, s);
          }
          _domReadHead = _domReadHead._next;
          if (_domReadHead == null) _stats.domReadEnd();
        }
        _domReadTail = null;
      } while (_domWriteHead != null || _domReadHead != null);
      _stats.flushEnd();
      assert((() {
        _stats.flushAssertStart();
        var digestLog = [];
        var flushLog = [];
        (_readWriteGroup as RootWatchGroup).detectChanges(
            changeLog: (s, c, p) => digestLog.add('$s: $c <= $p'),
            fieldStopwatch: _scopeStats.fieldStopwatch,
            evalStopwatch: _scopeStats.evalStopwatch,
            processStopwatch: _scopeStats.processStopwatch);
        (_readOnlyGroup as RootWatchGroup).detectChanges(
            changeLog: (s, c, p) => flushLog.add('$s: $c <= $p'),
            fieldStopwatch: _scopeStats.fieldStopwatch,
            evalStopwatch: _scopeStats.evalStopwatch,
            processStopwatch: _scopeStats.processStopwatch);
        if (digestLog.isNotEmpty || flushLog.isNotEmpty) {
          throw 'Observer reaction functions should not change model. \n'
                'These watch changes were detected: ${digestLog.join('; ')}\n'
                'These observe changes were detected: ${flushLog.join('; ')}';
        }
        _stats.flushAssertEnd();
        return true;
      })());
    } finally {
      _stats.cycleEnd();
      _transitionState(STATE_FLUSH, null);
    }
  }

  // QUEUES
  void runAsync(fn()) {
    var chain = new _FunctionChain(fn);
    if (_runAsyncHead == null) {
      _runAsyncHead = _runAsyncTail = chain;
    } else {
      _runAsyncTail = _runAsyncTail._next = chain;
    }
  }

  void domWrite(fn()) {
    var chain = new _FunctionChain(fn);
    if (_domWriteHead == null) {
      _domWriteHead = _domWriteTail = chain;
    } else {
      _domWriteTail = _domWriteTail._next = chain;
    }
  }

  void domRead(fn()) {
    var chain = new _FunctionChain(fn);
    if (_domReadHead == null) {
      _domReadHead = _domReadTail = chain;
    } else {
      _domReadTail = _domReadTail._next = chain;
    }
  }

  void destroy() {}

  void _transitionState(String from, String to) {
    assert(isAttached);
    if (_state != from) throw "$_state already in progress can not enter $to.";
    _state = to;
  }
}

/**
 * Keeps track of Streams for each Scope. When emitting events
 * we would need to walk the whole tree. Its faster if we can prune
 * the Scopes we have to visit.
 *
 * Scope with no [_ScopeStreams] has no events registered on itself or children
 *
 * We keep track of [Stream]s, and also child scope [Stream]s. To save
 * memory we use the same stream object on all of our parents if they don't
 * have one. But that means that we have to keep track if the stream belongs
 * to the node.
 *
 * Scope with [_ScopeStreams] but who's [_scope] does not match the scope
 * is only inherited
 *
 * Only [Scope] with [_ScopeStreams] who's [_scope] matches the [Scope]
 * instance is the actual scope.
 *
 * Once the [Stream] is created it can not be removed even if all listeners
 * are canceled. That is because we don't know if someone still has reference
 * to it.
 */
class _Streams {
  final ExceptionHandler _exceptionHandler;
  /// Scope we belong to.
  final Scope _scope;
  /// [Stream]s for [_scope] only
  final _streams = new Map<String, ScopeStream>();
  /// Child [Scope] event counts.
  final Map<String, int> _typeCounts;

  _Streams(this._scope, this._exceptionHandler, _Streams inheritStreams)
      : _typeCounts = inheritStreams == null
          ? <String, int>{}
          : new Map.from(inheritStreams._typeCounts);

  static ScopeEvent emit(Scope scope, String name, data) {
    var event = new ScopeEvent(name, scope, data);
    var scopeCursor = scope;
    while (scopeCursor != null) {
      if (scopeCursor._streams != null &&
          scopeCursor._streams._scope == scopeCursor) {
        ScopeStream stream = scopeCursor._streams._streams[name];
        if (stream != null) {
          event._currentScope = scopeCursor;
          stream._fire(event);
          if (event.propagationStopped) return event;
        }
      }
      scopeCursor = scopeCursor._parentScope;
    }
    return event;
  }

  static ScopeEvent broadcast(Scope scope, String name, data) {
    _Streams scopeStreams = scope._streams;
    var event = new ScopeEvent(name, scope, data);
    if (scopeStreams != null && scopeStreams._typeCounts.containsKey(name)) {
      var queue = new Queue()..addFirst(scopeStreams._scope);
      while (queue.isNotEmpty) {
        scope = queue.removeFirst();
        scopeStreams = scope._streams;
        assert(scopeStreams._scope == scope);
        if (scopeStreams._streams.containsKey(name)) {
          var stream = scopeStreams._streams[name];
          event._currentScope = scope;
          stream._fire(event);
        }
        // Reverse traversal so that when the queue is read it is correct order.
        var childScope = scope._childTail;
        while (childScope != null) {
          scopeStreams = childScope._streams;
          if (scopeStreams != null &&
              scopeStreams._typeCounts.containsKey(name)) {
            queue.addFirst(scopeStreams._scope);
          }
          childScope = childScope._prev;
        }
      }
    }
    return event;
  }

  static async.Stream<ScopeEvent> on(Scope scope,
                                     ExceptionHandler _exceptionHandler,
                                     String name) {
    _forceNewScopeStream(scope, _exceptionHandler);
    return scope._streams._get(scope, name);
  }

  static void _forceNewScopeStream(scope, _exceptionHandler) {
    _Streams streams = scope._streams;
    Scope scopeCursor = scope;
    bool splitMode = false;
    while (scopeCursor != null) {
      _Streams cursorStreams = scopeCursor._streams;
      var hasStream = cursorStreams != null;
      var hasOwnStream = hasStream && cursorStreams._scope == scopeCursor;
      if (hasOwnStream) return;

      if (!splitMode && (streams == null || (hasStream && !hasOwnStream))) {
        if (hasStream && !hasOwnStream) {
          splitMode = true;
        }
        streams = new _Streams(scopeCursor, _exceptionHandler, cursorStreams);
      }
      scopeCursor._streams = streams;
      scopeCursor = scopeCursor._parentScope;
    }
  }

  static void destroy(Scope scope) {
    var toBeDeletedStreams = scope._streams;
    if (toBeDeletedStreams == null) return; // no streams to clean up
    var parentScope = scope._parentScope; // skip current scope as not to delete listeners
    // find the parent-most scope which still has our stream to be deleted.
    while (parentScope != null && parentScope._streams == toBeDeletedStreams) {
      parentScope._streams = null;
      parentScope = parentScope._parentScope;
    }
    // At this point scope is the parent-most scope which has its own typeCounts
    if (parentScope == null) return;
    var parentStreams = parentScope._streams;
    assert(parentStreams != toBeDeletedStreams);
    // remove typeCounts from the scope to be destroyed from the parent
    // typeCounts
    toBeDeletedStreams._typeCounts.forEach(
        (name, count) => parentStreams._addCount(name, -count));
  }

  async.Stream _get(Scope scope, String name) {
    assert(scope._streams == this);
    assert(scope._streams._scope == scope);
    assert(_exceptionHandler != null);
    return _streams.putIfAbsent(name, () =>
        new ScopeStream(this, _exceptionHandler, name));
  }

  void _addCount(String name, int amount) {
    // decrement the counters on all parent scopes
    _Streams lastStreams = null;
    var scope = _scope;
    while (scope != null) {
      if (lastStreams != scope._streams) {
        // we have a transition, need to decrement it
        lastStreams = scope._streams;
        int count = lastStreams._typeCounts[name];
        count = count == null ? amount : count + amount;
        assert(count >= 0);
        if (count == 0) {
          lastStreams._typeCounts.remove(name);
          if (_scope == scope) _streams.remove(name);
        } else {
          lastStreams._typeCounts[name] = count;
        }
      }
      scope = scope._parentScope;
    }
  }
}

class ScopeStream extends async.Stream<ScopeEvent> {
  final ExceptionHandler _exceptionHandler;
  final _Streams _streams;
  final String _name;
  final subscriptions = <ScopeStreamSubscription>[];
  final List<Function> _work = <Function>[];
  bool _firing = false;


  ScopeStream(this._streams, this._exceptionHandler, this._name);

  ScopeStreamSubscription listen(void onData(ScopeEvent event),
                                 { Function onError,
                                   void onDone(),
                                   bool cancelOnError }) {
    var subscription = new ScopeStreamSubscription(this, onData);
    _concurrentSafeWork(() {
      if (subscriptions.isEmpty) _streams._addCount(_name, 1);
      subscriptions.add(subscription);
    });
    return subscription;
  }

  void _concurrentSafeWork([fn]) {
    if (fn != null) _work.add(fn);
    while(!_firing && _work.isNotEmpty) {
      _work.removeLast()();
    }
  }

  void _fire(ScopeEvent event) {
    _firing = true;
    try {
      for (ScopeStreamSubscription subscription in subscriptions) {
        try {
          subscription._onData(event);
        } catch (e, s) {
          _exceptionHandler(e, s);
        }
      }
    } finally {
      _firing = false;
      _concurrentSafeWork();
    }
  }

  void _remove(ScopeStreamSubscription subscription) {
    _concurrentSafeWork(() {
      assert(subscription._scopeStream == this);
      if (subscriptions.remove(subscription)) {
        if (subscriptions.isEmpty) _streams._addCount(_name, -1);
      } else {
        throw new StateError('AlreadyCanceled');
      }
    });
  }
}

class ScopeStreamSubscription implements async.StreamSubscription<ScopeEvent> {
  final ScopeStream _scopeStream;
  final Function _onData;
  ScopeStreamSubscription(this._scopeStream, this._onData);

  async.Future cancel() {
    _scopeStream._remove(this);
    return null;
  }

  void onData(void handleData(ScopeEvent data)) => _NOT_IMPLEMENTED();
  void onError(Function handleError) => _NOT_IMPLEMENTED();
  void onDone(void handleDone()) => _NOT_IMPLEMENTED();
  void pause([async.Future resumeSignal]) => _NOT_IMPLEMENTED();
  void resume() => _NOT_IMPLEMENTED();
  bool get isPaused => _NOT_IMPLEMENTED();
  async.Future asFuture([var futureValue]) => _NOT_IMPLEMENTED();
}

_NOT_IMPLEMENTED() {
  throw new StateError('Not Implemented');
}


class _FunctionChain {
  final Function fn;
  _FunctionChain _next;

  _FunctionChain(fn()): fn = fn {
    assert(fn != null);
  }
}

class _AstParser {
  final Parser _parser;
  int _id = 0;
  final ExpressionVisitor _visitor;

  _AstParser(this._parser, ClosureMap closureMap)
      : _visitor = new ExpressionVisitor(closureMap);

  AST call(String input, {FormatterMap formatters,
                          bool collection: false,
                          Object context: null }) {
    _visitor.formatters = formatters;
    AST contextRef = _visitor.contextRef;
    try {
      if (context != null) {
        _visitor.contextRef = new ConstantAST(context, '#${_id++}');
      }
      var exp = _parser(input);
      return collection ? _visitor.visitCollection(exp) : _visitor.visit(exp);
    } finally {
      _visitor.contextRef = contextRef;
      _visitor.formatters = null;
    }
  }
}

class ExpressionVisitor implements syntax.Visitor {
  static final ContextReferenceAST scopeContextRef = new ContextReferenceAST();
  final ClosureMap _closureMap;
  AST contextRef = scopeContextRef;


  ExpressionVisitor(this._closureMap);

  AST ast;
  FormatterMap formatters;

  AST visit(syntax.Expression exp) {
    exp.accept(this);
    assert(ast != null);
    try {
      return ast;
    } finally {
      ast = null;
    }
  }

  AST visitCollection(syntax.Expression exp) => new CollectionAST(visit(exp));
  AST _mapToAst(syntax.Expression expression) => visit(expression);

  List<AST> _toAst(List<syntax.Expression> expressions) =>
      expressions.map(_mapToAst).toList();

  Map<Symbol, AST> _toAstMap(Map<String, syntax.Expression> expressions) {
    if (expressions.isEmpty) return const {};
    Map<Symbol, AST> result = new Map<Symbol, AST>();
    expressions.forEach((String name, syntax.Expression expression) {
      result[_closureMap.lookupSymbol(name)] = _mapToAst(expression);
    });
    return result;
  }

  void visitCallScope(syntax.CallScope exp) {
    List<AST> positionals = _toAst(exp.arguments.positionals);
    Map<Symbol, AST> named = _toAstMap(exp.arguments.named);
    ast = new MethodAST(contextRef, exp.name, positionals, named);
  }
  void visitCallMember(syntax.CallMember exp) {
    List<AST> positionals = _toAst(exp.arguments.positionals);
    Map<Symbol, AST> named = _toAstMap(exp.arguments.named);
    ast = new MethodAST(visit(exp.object), exp.name, positionals, named);
  }
  void visitAccessScope(syntax.AccessScope exp) {
    ast = new FieldReadAST(contextRef, exp.name);
  }
  void visitAccessMember(syntax.AccessMember exp) {
    ast = new FieldReadAST(visit(exp.object), exp.name);
  }
  void visitBinary(syntax.Binary exp) {
    ast = new PureFunctionAST(exp.operation,
                              _operationToFunction(exp.operation),
                              [visit(exp.left), visit(exp.right)]);
  }
  void visitPrefix(syntax.Prefix exp) {
    ast = new PureFunctionAST(exp.operation,
                              _operationToFunction(exp.operation),
                              [visit(exp.expression)]);
  }
  void visitConditional(syntax.Conditional exp) {
    ast = new PureFunctionAST('?:', _operation_ternary,
                              [visit(exp.condition), visit(exp.yes),
                              visit(exp.no)]);
  }
  void visitAccessKeyed(syntax.AccessKeyed exp) {
    ast = new ClosureAST('[]', _operation_bracket,
                             [visit(exp.object), visit(exp.key)]);
  }
  void visitLiteralPrimitive(syntax.LiteralPrimitive exp) {
    ast = new ConstantAST(exp.value);
  }
  void visitLiteralString(syntax.LiteralString exp) {
    ast = new ConstantAST(exp.value);
  }
  void visitLiteralArray(syntax.LiteralArray exp) {
    List<AST> items = _toAst(exp.elements);
    ast = new PureFunctionAST('[${items.join(', ')}]', new ArrayFn(), items);
  }

  void visitLiteralObject(syntax.LiteralObject exp) {
    List<String> keys = exp.keys;
    List<AST> values = _toAst(exp.values);
    assert(keys.length == values.length);
    var kv = <String>[];
    for (var i = 0; i < keys.length; i++) {
      kv.add('${keys[i]}: ${values[i]}');
    }
    ast = new PureFunctionAST('{${kv.join(', ')}}', new MapFn(keys), values);
  }

  void visitFormatter(syntax.Formatter exp) {
    if (formatters == null) {
      throw new Exception("No formatters have been registered");
    }
    Function formatterFunction = formatters(exp.name);
    List<AST> args = [visitCollection(exp.expression)];
    args.addAll(_toAst(exp.arguments).map((ast) => new CollectionAST(ast)));
    ast = new PureFunctionAST('|${exp.name}',
        new _FormatterWrapper(formatterFunction, args.length), args);
  }

  // TODO(misko): this is a corner case. Choosing not to implement for now.
  void visitCallFunction(syntax.CallFunction exp) {
    _notSupported("function's returing functions");
  }
  void visitAssign(syntax.Assign exp) {
    _notSupported('assignement');
  }
  void visitLiteral(syntax.Literal exp) {
    _notSupported('literal');
  }
  void visitExpression(syntax.Expression exp) {
    _notSupported('?');
  }
  void visitChain(syntax.Chain exp) {
    _notSupported(';');
  }

  void  _notSupported(String name) {
    throw new StateError("Can not watch expression containing '$name'.");
  }
}

Function _operationToFunction(String operation) {
  switch(operation) {
    case '!'  : return _operation_negate;
    case '+'  : return _operation_add;
    case '-'  : return _operation_subtract;
    case '*'  : return _operation_multiply;
    case '/'  : return _operation_divide;
    case '~/' : return _operation_divide_int;
    case '%'  : return _operation_remainder;
    case '==' : return _operation_equals;
    case '!=' : return _operation_not_equals;
    case '<'  : return _operation_less_then;
    case '>'  : return _operation_greater_then;
    case '<=' : return _operation_less_or_equals_then;
    case '>=' : return _operation_greater_or_equals_then;
    case '^'  : return _operation_power;
    case '&'  : return _operation_bitwise_and;
    case '&&' : return _operation_logical_and;
    case '||' : return _operation_logical_or;
    default: throw new StateError(operation);
  }
}

_operation_negate(value)                       => !toBool(value);
_operation_add(left, right)                    => autoConvertAdd(left, right);
_operation_subtract(left, right)               => (left != null && right != null) ? left - right : (left != null ? left : (right != null ? 0 - right : 0));
_operation_multiply(left, right)               => (left == null || right == null) ? null : left * right;
_operation_divide(left, right)                 => (left == null || right == null) ? null : left / right;
_operation_divide_int(left, right)             => (left == null || right == null) ? null : left ~/ right;
_operation_remainder(left, right)              => (left == null || right == null) ? null : left % right;
_operation_equals(left, right)                 => left == right;
_operation_not_equals(left, right)             => left != right;
_operation_less_then(left, right)              => (left == null || right == null) ? null : left < right;
_operation_greater_then(left, right)           => (left == null || right == null) ? null : left > right;
_operation_less_or_equals_then(left, right)    => (left == null || right == null) ? null : left <= right;
_operation_greater_or_equals_then(left, right) => (left == null || right == null) ? null : left >= right;
_operation_power(left, right)                  => (left == null || right == null) ? null : left ^ right;
_operation_bitwise_and(left, right)            => (left == null || right == null) ? null : left & right;
// TODO(misko): these should short circuit the evaluation.
_operation_logical_and(left, right)            => toBool(left) && toBool(right);
_operation_logical_or(left, right)             => toBool(left) || toBool(right);

_operation_ternary(condition, yes, no) => toBool(condition) ? yes : no;
_operation_bracket(obj, key) => obj == null ? null : obj[key];

class ArrayFn extends FunctionApply {
  // TODO(misko): figure out why do we need to make a copy?
  apply(List args) => new List.from(args);
}

class MapFn extends FunctionApply {
  final List<String> keys;

  MapFn(this.keys);

  Map apply(List values) {
    // TODO(misko): figure out why do we need to make a copy instead of reusing instance?
    assert(values.length == keys.length);
    return new Map.fromIterables(keys, values);
  }
}

class _FormatterWrapper extends FunctionApply {
  final Function formatterFn;
  final List args;
  final List<Watch> argsWatches;
  _FormatterWrapper(this.formatterFn, length):
      args = new List(length),
      argsWatches = new List(length);

  apply(List values) {
    for (var i=0; i < values.length; i++) {
      var value = values[i];
      var lastValue = args[i];
      if (!identical(value, lastValue)) {
       if (value is CollectionChangeRecord) {
         args[i] = (value as CollectionChangeRecord).iterable;
       } else if (value is MapChangeRecord) {
         args[i] = (value as MapChangeRecord).map;
       } else {
         args[i] = value;
       }
      }
    }
    var value = Function.apply(formatterFn, args);
    if (value is Iterable) {
      // Since formatters are pure we can guarantee that this well never change.
      // By wrapping in UnmodifiableListView we can hint to the dirty checker
      // and short circuit the iterator.
      value = new UnmodifiableListView(value);
    }
    return value;
  }
}
