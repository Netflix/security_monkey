library dirty_checking_change_detector;

import 'dart:collection';
import 'package:angular/change_detection/change_detection.dart';

/**
 * [DirtyCheckingChangeDetector] determines which object properties have changed
 * by comparing them to the their previous value.
 *
 * GOALS:
 *   - Plugable implementation, replaceable with other technologies, such as
 *     Object.observe().
 *   - SPEED this needs to be as fast as possible.
 *   - No GC pressure. Since change detection runs often it should perform no
 *     memory allocations.
 *   - The changes need to be delivered in a single data-structure at once.
 *     There are two reasons for this:
 *       1. It should be easy to measure the cost of change detection vs
 *          processing.
 *       2. The feature may move to VM for performance reason. The VM should be
 *          free to implement it in any way. The only requirement is that the
 *          list of changes need to be delivered.
 *
 * [DirtyCheckingRecord]
 *
 * Each property to be watched is recorded as a [DirtyCheckingRecord] and kept
 * in a linked list. Linked list are faster than Arrays for iteration. They also
 * allow removal of large blocks of watches in an efficient manner.
 */
class DirtyCheckingChangeDetectorGroup<H> implements ChangeDetectorGroup<H> {
  /**
   * A group must have at least one record so that it can act as a placeholder.
   * This record has minimal cost and never detects change. Once actual records
   * get added the marker record gets removed, but it gets reinserted if all
   * other records are removed.
   */
  final DirtyCheckingRecord _marker = new DirtyCheckingRecord.marker();

  final FieldGetterFactory _fieldGetterFactory;

  /**
   * All records for group are kept together and are denoted by head/tail.
   * The [_recordHead]-[_recordTail] only include our own records. If you want
   * to see our childGroup records as well use
   * [_head]-[_childInclRecordTail].
   */
  DirtyCheckingRecord _recordHead, _recordTail;

  /**
   * Same as [_tail] but includes child-group records as well.
   */
  DirtyCheckingRecord get _childInclRecordTail {
    DirtyCheckingChangeDetectorGroup tail = this, nextTail;
    while ((nextTail = tail._childTail) != null) {
      tail = nextTail;
    }
    return tail._recordTail;
  }

  bool get isAttached {
    DirtyCheckingChangeDetectorGroup current = this;
    DirtyCheckingChangeDetectorGroup parent;
    while ((parent = current._parent) != null) {
      current = parent;
    }
    return current is DirtyCheckingChangeDetector
      ? true
      : current._prev != null && current._next != null;
  }


  DirtyCheckingChangeDetector get _root {
    var root = this;
    var parent;
    while ((parent = root._parent) != null) {
      root = parent;
    }
    return root is DirtyCheckingChangeDetector ? root : null;
  }

  /**
   * ChangeDetectorGroup is organized hierarchically, a root group can have
   * child groups and so on. We keep track of parent, children and next,
   * previous here.
   */
  DirtyCheckingChangeDetectorGroup _parent, _childHead, _childTail, _prev, _next;

  DirtyCheckingChangeDetectorGroup(this._parent, this._fieldGetterFactory) {
    // we need to insert the marker record at the beginning.
    if (_parent == null) {
      _recordHead = _marker;
      _recordTail = _marker;
    } else {
      _recordTail = _parent._childInclRecordTail;
      // _recordAdd uses _recordTail from above.
      _recordHead = _recordTail = _recordAdd(_marker);
    }
  }

  /**
   * Returns the number of watches in this group (including child groups).
   */
  get count {
    int count = 0;
    DirtyCheckingRecord cursor = _recordHead;
    DirtyCheckingRecord end = _childInclRecordTail;
    while (cursor != null) {
      if (cursor._mode != DirtyCheckingRecord._MODE_MARKER_) {
        count++;
      }
      if (cursor == end) break;
      cursor = cursor._nextRecord;
    }
    return count;
  }

  WatchRecord<H> watch(Object object, String field, H handler) {
    assert(_root != null); // prove that we are not deleted connected;
    return _recordAdd(new DirtyCheckingRecord(this, _fieldGetterFactory,
                                              handler, field, object));
  }

  /**
   * Create a child [ChangeDetector] group.
   */
  DirtyCheckingChangeDetectorGroup<H> newGroup() {
    // Disabled due to issue https://github.com/angular/angular.dart/issues/812
    // assert(_root._assertRecordsOk());
    var child = new DirtyCheckingChangeDetectorGroup(this, _fieldGetterFactory);
    if (_childHead == null) {
      _childHead = _childTail = child;
    } else {
      child._prev = _childTail;
      _childTail._next = child;
      _childTail = child;
    }
    // Disabled due to issue https://github.com/angular/angular.dart/issues/812
    // assert(_root._assertRecordsOk());
    return child;
  }

  /**
   * Bulk remove all records.
   */
  void remove() {
    var root;
    assert((root = _root) != null);
    assert(root._assertRecordsOk());
    DirtyCheckingRecord prevRecord = _recordHead._prevRecord;
    var childInclRecordTail = _childInclRecordTail;
    DirtyCheckingRecord nextRecord = childInclRecordTail._nextRecord;

    if (prevRecord != null) prevRecord._nextRecord = nextRecord;
    if (nextRecord != null) nextRecord._prevRecord = prevRecord;

    var prevGroup = _prev;
    var nextGroup = _next;

    if (prevGroup == null) {
      _parent._childHead = nextGroup;
    } else {
      prevGroup._next = nextGroup;
    }
    if (nextGroup == null) {
      _parent._childTail = prevGroup;
    } else {
      nextGroup._prev = prevGroup;
    }
    _parent = null;
    _prev = _next = null;
    _recordHead._prevRecord = null;
    childInclRecordTail._nextRecord = null;
    assert(root._assertRecordsOk());
  }

  DirtyCheckingRecord _recordAdd(DirtyCheckingRecord record) {
    DirtyCheckingRecord previous = _recordTail;
    DirtyCheckingRecord next = previous == null ? null : previous._nextRecord;

    record._nextRecord = next;
    record._prevRecord = previous;

    if (previous != null) previous._nextRecord = record;
    if (next != null) next._prevRecord = record;

    _recordTail = record;

    if (previous == _marker) _recordRemove(_marker);

    return record;
  }

  void _recordRemove(DirtyCheckingRecord record) {
    DirtyCheckingRecord previous = record._prevRecord;
    DirtyCheckingRecord next = record._nextRecord;

    if (record == _recordHead && record == _recordTail) {
      // we are the last one, must leave marker behind.
      _recordHead = _recordTail = _marker;
      _marker._nextRecord = next;
      _marker._prevRecord = previous;
      if (previous != null) previous._nextRecord = _marker;
      if (next != null) next._prevRecord = _marker;
    } else {
      if (record == _recordTail) _recordTail = previous;
      if (record == _recordHead) _recordHead = next;
      if (previous != null) previous._nextRecord = next;
      if (next != null) next._prevRecord = previous;
    }
  }

  String toString() {
    var lines = [];
    if (_parent == null) {
      var allRecords = [];
      DirtyCheckingRecord record = _recordHead;
      var includeChildrenTail = _childInclRecordTail;
      do {
        allRecords.add(record.toString());
        record = record._nextRecord;
      } while (record != includeChildrenTail);
      allRecords.add(includeChildrenTail);
      lines.add('FIELDS: ${allRecords.join(', ')}');
    }

    var records = [];
    DirtyCheckingRecord record = _recordHead;
    while (record != _recordTail) {
      records.add(record.toString());
      record = record._nextRecord;
    }
    records.add(record.toString());

    lines.add('DirtyCheckingChangeDetectorGroup(fields: ${records.join(', ')})');
    var childGroup = _childHead;
    while (childGroup != null) {
      lines.add('  ' + childGroup.toString().split('\n').join('\n  '));
      childGroup = childGroup._next;
    }
    return lines.join('\n');
  }
}

class DirtyCheckingChangeDetector<H> extends DirtyCheckingChangeDetectorGroup<H>
    implements ChangeDetector<H> {

  final DirtyCheckingRecord _fakeHead = new DirtyCheckingRecord.marker();

  DirtyCheckingChangeDetector(FieldGetterFactory fieldGetterFactory)
      : super(null, fieldGetterFactory);

  DirtyCheckingChangeDetector get _root => this;

  _assertRecordsOk() {
    var record = this._recordHead;
    var groups = [this];
    DirtyCheckingChangeDetectorGroup group;
    while (groups.isNotEmpty) {
      group = groups.removeAt(0);
      DirtyCheckingChangeDetectorGroup childGroup = group._childTail;
      while (childGroup != null) {
        groups.insert(0, childGroup);
        childGroup = childGroup._prev;
      }
      var groupRecord = group._recordHead;
      var groupLast = group._recordTail;
      if (record != groupRecord) {
        throw "Next record is $record expecting $groupRecord";
      }
      var done = false;
      while (!done && groupRecord != null) {
        if (groupRecord == record) {
          if (record._group != null && record._group != group) {
            throw "Wrong group: $record "
                  "Got ${record._group} Expecting: $group";
          }
          record = record._nextRecord;
        } else {
          throw 'lost: $record found $groupRecord\n$this';
        }

        if (groupRecord._nextRecord != null &&
            groupRecord._nextRecord._prevRecord != groupRecord) {
          throw "prev/next pointer missmatch on "
                "$groupRecord -> ${groupRecord._nextRecord} "
                "<= ${groupRecord._nextRecord._prevRecord} in $this";
        }
        if (groupRecord._prevRecord != null &&
            groupRecord._prevRecord._nextRecord != groupRecord) {
              throw "prev/next pointer missmatch on "
                    "$groupRecord -> ${groupRecord._prevRecord} "
                    "<= ${groupRecord._prevRecord._nextChange} in $this";
        }
        if (groupRecord == groupLast) {
          done = true;
        }
        groupRecord = groupRecord._nextRecord;
      }
    }
    if(record != null) {
      throw "Extra records at tail: $record on $this";
    }
    return true;
  }

  Iterator<Record<H>> collectChanges({EvalExceptionHandler exceptionHandler,
                                      AvgStopwatch stopwatch}) {
    if (stopwatch != null) stopwatch.start();
    DirtyCheckingRecord changeTail = _fakeHead;
    DirtyCheckingRecord current = _recordHead; // current index

    int count = 0;
    while (current != null) {
      try {
        if (current.check()) changeTail = changeTail._nextChange = current;
        count++;
      } catch (e, s) {
        if (exceptionHandler == null) {
          rethrow;
        } else {
          exceptionHandler(e, s);
        }
      }
      current = current._nextRecord;
    }

    changeTail._nextChange = null;
    if (stopwatch != null) stopwatch..stop()..increment(count);
    DirtyCheckingRecord changeHead = _fakeHead._nextChange;
    _fakeHead._nextChange = null;

    return new _ChangeIterator(changeHead);
  }

  void remove() {
    throw new StateError('Root ChangeDetector can not be removed');
  }
}

class _ChangeIterator<H> implements Iterator<Record<H>>{
  DirtyCheckingRecord _current;
  DirtyCheckingRecord _next;
  DirtyCheckingRecord get current => _current;

  _ChangeIterator(this._next);

  bool moveNext() {
    _current = _next;
    if (_next != null) {
      _next = _current._nextChange;
      /*
       * This is important to prevent memory leaks. If we don't reset then
       * a record maybe pointing to a deleted change detector group and it
       * will not release the reference until it fires again. So we have
       * to be eager about releasing references.
       */
      _current._nextChange = null;
    }
    return _current != null;
  }
}

/**
 * [DirtyCheckingRecord] represents as single item to check. The heart of the
 * [DirtyCheckingRecord] is a the [check] method which can read the
 * [currentValue] and compare it to the [previousValue].
 *
 * [DirtyCheckingRecord]s form linked list. This makes traversal, adding, and
 * removing efficient. [DirtyCheckingRecord] also has a [nextChange] field which
 * creates a single linked list of all of the changes for efficient traversal.
 */
class DirtyCheckingRecord<H> implements Record<H>, WatchRecord<H> {
  static const List<String> _MODE_NAMES = const [
      'MARKER',
      'NOOP',
      'IDENTITY',
      'GETTER',
      'GETTER / CLOSURE'
      'MAP[]',
      'ITERABLE',
      'MAP'];
  static const int _MODE_MARKER_ = 0;
  static const int _MODE_NOOP_ = 1;
  static const int _MODE_IDENTITY_ = 2;
  static const int _MODE_GETTER_ = 3;
  static const int _MODE_GETTER_OR_METHOD_CLOSURE_ = 4;
  static const int _MODE_MAP_FIELD_ = 5;
  static const int _MODE_ITERABLE_ = 6;
  static const int _MODE_MAP_ = 7;

  final DirtyCheckingChangeDetectorGroup _group;
  final FieldGetterFactory _fieldGetterFactory;
  final String field;
  final H handler;

  int _mode;

  var previousValue;
  var currentValue;
  DirtyCheckingRecord<H> _nextRecord;
  DirtyCheckingRecord<H> _prevRecord;
  Record<H> _nextChange;
  var _object;
  FieldGetter _getter;

  DirtyCheckingRecord(this._group, this._fieldGetterFactory, this.handler,
                      this.field, _object) {
    object = _object;
  }

  DirtyCheckingRecord.marker()
      : _group = null,
        _fieldGetterFactory = null,
        handler = null,
        field = null,
        _getter = null,
        _mode = _MODE_MARKER_;

  dynamic get object => _object;

  /**
   * Setting an [object] will cause the setter to introspect it and place
   * [DirtyCheckingRecord] into different access modes. If Object it sets up
   * reflection. If [Map] then it sets up map accessor.
   */
  void set object(obj) {
    _object = obj;
    if (obj == null) {
      _mode = _MODE_IDENTITY_;
      _getter = null;
      return;
    }

    if (field == null) {
      _getter = null;
      if (obj is Map) {
        if (_mode != _MODE_MAP_) {
          _mode =  _MODE_MAP_;
          currentValue = new _MapChangeRecord();
        }
        if (currentValue.isDirty) {
          // We're dirty because the mapping we tracked by reference mutated.
          // In addition, our reference has now changed.  We should compare the
          // previous reported value of that mapping with the one from the
          // new reference.
          currentValue._revertToPreviousState();
        }

      } else if (obj is Iterable) {
        if (_mode != _MODE_ITERABLE_) {
          _mode = _MODE_ITERABLE_;
          currentValue = new _CollectionChangeRecord();
        }
        if (currentValue.isDirty) {
          // We're dirty because the collection we tracked by reference mutated.
          // In addition, our reference has now changed.  We should compare the
          // previous reported value of that collection with the one from the
          // new reference.
          currentValue._revertToPreviousState();
        }
      } else {
        _mode = _MODE_IDENTITY_;
      }

      return;
    }

    if (obj is Map) {
      _mode =  _MODE_MAP_FIELD_;
      _getter = null;
    } else {
      _mode = _MODE_GETTER_OR_METHOD_CLOSURE_;
      _getter = _fieldGetterFactory.getter(obj, field);
    }
  }

  bool check() {
    assert(_mode != null);
    var current;
    switch (_mode) {
      case _MODE_MARKER_:
        return false;
      case _MODE_NOOP_:
        return false;
      case _MODE_GETTER_:
        current = _getter(object);
        break;
      case _MODE_GETTER_OR_METHOD_CLOSURE_:
        // NOTE: When Dart looks up a method "foo" on object "x", it returns a
        // new closure for each lookup.  They compare equal via "==" but are no
        // identical().  There's no point getting a new value each time and
        // decide it's the same so we'll skip further checking after the first
        // time.
        current = _getter(object);
        if (current is Function && !identical(current, _getter(object))) {
          _mode = _MODE_NOOP_;
        } else {
          _mode = _MODE_GETTER_;
        }
        break;
      case _MODE_MAP_FIELD_:
        current = object[field];
        break;
      case _MODE_IDENTITY_:
        current = object;
        _mode = _MODE_NOOP_;
        break;
      case _MODE_MAP_:
        return (currentValue as _MapChangeRecord)._check(object);
      case _MODE_ITERABLE_:
        return (currentValue as _CollectionChangeRecord)._check(object);
      default:
        assert(false);
    }

    var last = currentValue;
    if (!identical(last, current)) {
      if (last is String && current is String &&
          last == current) {
        // This is false change in strings we need to recover, and pretend it
        // is the same. We save the value so that next time identity will pass
        currentValue = current;
      } else if (last is num && last.isNaN && current is num && current.isNaN) {
        // we need this for the compiled JavaScript since in JS NaN !== NaN.
      } else {
        previousValue = last;
        currentValue = current;
        return true;
      }
    }
    return false;
  }


  void remove() {
    _group._recordRemove(this);
  }

  String toString() =>
      '${_mode < _MODE_NAMES.length ?  _MODE_NAMES[_mode] : '?'}[$field]{$hashCode}';
}

final Object _INITIAL_ = new Object();

class _MapChangeRecord<K, V> implements MapChangeRecord<K, V> {
  final _records = new Map<dynamic, KeyValueRecord>();
  Map _map;

  Map get map => _map;

  KeyValueRecord<K, V> _mapHead;
  KeyValueRecord<K, V> _previousMapHead;
  KeyValueRecord<K, V> _changesHead, _changesTail;
  KeyValueRecord<K, V> _additionsHead, _additionsTail;
  KeyValueRecord<K, V> _removalsHead, _removalsTail;

  get isDirty => _additionsHead != null ||
                 _changesHead != null ||
                 _removalsHead != null;

  _revertToPreviousState() {
    if (!isDirty) {
      return;
    }
    KeyValueRecord record, prev;
    int i = 0;
    for (record = _mapHead = _previousMapHead;
         record != null;
         prev = record, record = record._nextPrevious, ++i) {
      record._currentValue = record._previousValue;
      if (prev != null) {
        prev._next = prev._nextPrevious = record;
      }
    }
    prev._next = null;
    _undoDeltas();
  }

  KeyValueRecord<K, V> r;

  void forEachItem(void f(MapKeyValue<K, V> change)) {
    for (r = _mapHead; r != null; r = r._next) {
      f(r);
    }
  }

  void forEachPreviousItem(void f(MapKeyValue<K, V> change)) {
    for (r = _previousMapHead; r != null; r = r._nextPrevious) {
      f(r);
    }
  }

  void forEachChange(void f(MapKeyValue<K, V> change)) {
    for (r = _changesHead; r != null; r = r._nextChanged) {
      f(r);
    }
  }

  void forEachAddition(void f(MapKeyValue<K, V> addition)){
    for (r = _additionsHead; r != null; r = r._nextAdded) {
      f(r);
    }
  }

  void forEachRemoval(void f(MapKeyValue<K, V> removal)){
    for (r = _removalsHead; r != null; r = r._nextRemoved) {
      f(r);
    }
  }

  bool _check(Map map) {
    _reset();
    _map = map;
    Map records = _records;
    KeyValueRecord oldSeqRecord = _mapHead;
    KeyValueRecord lastOldSeqRecord;
    KeyValueRecord lastNewSeqRecord;
    var seqChanged = false;
    map.forEach((key, value) {
      var newSeqRecord;
      if (oldSeqRecord != null && key == oldSeqRecord.key) {
        newSeqRecord = oldSeqRecord;
        if (!identical(value, oldSeqRecord._currentValue)) {
          var prev = oldSeqRecord._previousValue = oldSeqRecord._currentValue;
          oldSeqRecord._currentValue = value;
          if (!((value is String && prev is String && value == prev) ||
                (value is num && value.isNaN && prev is num && prev.isNaN))) {
            // Check string by value rather than reference
            _addToChanges(oldSeqRecord);
          }
        }
      } else {
        seqChanged = true;
        if (oldSeqRecord != null) {
          oldSeqRecord._next = null;
          _removeFromSeq(lastOldSeqRecord, oldSeqRecord);
          _addToRemovals(oldSeqRecord);
        }
        if (records.containsKey(key)) {
          newSeqRecord = records[key];
        } else {
          newSeqRecord = records[key] = new KeyValueRecord(key);
          newSeqRecord._currentValue = value;
          _addToAdditions(newSeqRecord);
        }
      }

      if (seqChanged) {
        if (_isInRemovals(newSeqRecord)) {
          _removeFromRemovals(newSeqRecord);
        }
        if (lastNewSeqRecord == null) {
          _mapHead = newSeqRecord;
        } else {
          lastNewSeqRecord._next = newSeqRecord;
        }
      }
      lastOldSeqRecord = oldSeqRecord;
      lastNewSeqRecord = newSeqRecord;
      oldSeqRecord = oldSeqRecord == null ? null : oldSeqRecord._next;
    });
    _truncate(lastOldSeqRecord, oldSeqRecord);
    return isDirty;
  }

  void _reset() {
    if (isDirty) {
      // Record the state of the mapping for a possible _revertToPreviousState()
      for (KeyValueRecord record = _previousMapHead = _mapHead;
           record != null;
           record = record._next) {
        record._nextPrevious = record._next;
      }
      _undoDeltas();
    }
  }

  void _undoDeltas() {
    KeyValueRecord<K, V> r;

    for (r = _changesHead; r != null; r = r._nextChanged) {
      r._previousValue = r._currentValue;
    }

    for (r = _additionsHead; r != null; r = r._nextAdded) {
      r._previousValue = r._currentValue;
    }

    assert((() {
      var r = _changesHead;
      while (r != null) {
        var nextRecord = r._nextChanged;
        r._nextChanged = null;
        r = nextRecord;
      }

      r = _additionsHead;
      while (r != null) {
        var nextRecord = r._nextAdded;
        r._nextAdded = null;
        r = nextRecord;
      }

      r = _removalsHead;
      while (r != null) {
        var nextRecord = r._nextRemoved;
        r._nextRemoved = null;
        r = nextRecord;
      }

      return true;
    })());
    _changesHead = _changesTail = null;
    _additionsHead = _additionsTail = null;
    _removalsHead = _removalsTail = null;
  }

  void _truncate(KeyValueRecord lastRecord, KeyValueRecord record) {
    while (record != null) {
      if (lastRecord == null) {
        _mapHead = null;
      } else {
        lastRecord._next = null;
      }
      var nextRecord = record._next;
      assert((() {
        record._next = null;
        return true;
      })());
      _addToRemovals(record);
      lastRecord = record;
      record = nextRecord;
    }

    for (var r = _removalsHead; r != null; r = r._nextRemoved) {
      r._previousValue = r._currentValue;
      r._currentValue = null;
      _records.remove(r.key);
    }
  }

  bool _isInRemovals(KeyValueRecord record) =>
      record == _removalsHead ||
      record._nextRemoved != null ||
      record._prevRemoved != null;

  void _addToRemovals(KeyValueRecord record) {
    assert(record._next == null);
    assert(record._nextAdded == null);
    assert(record._nextChanged == null);
    assert(record._nextRemoved == null);
    assert(record._prevRemoved == null);
    if (_removalsHead == null) {
      _removalsHead = _removalsTail = record;
    } else {
      _removalsTail._nextRemoved = record;
      record._prevRemoved = _removalsTail;
      _removalsTail = record;
    }
  }

  void _removeFromSeq(KeyValueRecord prev, KeyValueRecord record) {
    KeyValueRecord next = record._next;
    if (prev == null) {
      _mapHead = next;
    } else {
      prev._next = next;
    }
    assert((() {
      record._next = null;
      return true;
    })());
  }

  void _removeFromRemovals(KeyValueRecord record) {
    assert(record._next == null);
    assert(record._nextAdded == null);
    assert(record._nextChanged == null);

    var prev = record._prevRemoved;
    var next = record._nextRemoved;
    if (prev == null) {
      _removalsHead = next;
    } else {
      prev._nextRemoved = next;
    }
    if (next == null) {
      _removalsTail = prev;
    } else {
      next._prevRemoved = prev;
    }
    record._prevRemoved = record._nextRemoved = null;
  }

  void _addToAdditions(KeyValueRecord record) {
    assert(record._next == null);
    assert(record._nextAdded == null);
    assert(record._nextChanged == null);
    assert(record._nextRemoved == null);
    assert(record._prevRemoved == null);
    if (_additionsHead == null) {
      _additionsHead = _additionsTail = record;
    } else {
      _additionsTail._nextAdded = record;
      _additionsTail = record;
    }
  }

  void _addToChanges(KeyValueRecord record) {
    assert(record._nextAdded == null);
    assert(record._nextChanged == null);
    assert(record._nextRemoved == null);
    assert(record._prevRemoved == null);
    if (_changesHead == null) {
      _changesHead = _changesTail = record;
    } else {
      _changesTail._nextChanged = record;
      _changesTail = record;
    }
  }

  String toString() {
    List itemsList = [], previousList = [], changesList = [], additionsList = [], removalsList = [];
    KeyValueRecord<K, V> r;
    for (r = _mapHead; r != null; r = r._next) {
      itemsList.add("$r");
    }
    for (r = _previousMapHead; r != null; r = r._nextPrevious) {
      previousList.add("$r");
    }
    for (r = _changesHead; r != null; r = r._nextChanged) {
      changesList.add("$r");
    }
    for (r = _additionsHead; r != null; r = r._nextAdded) {
      additionsList.add("$r");
    }
    for (r = _removalsHead; r != null; r = r._nextRemoved) {
      removalsList.add("$r");
    }
    return """
map: ${itemsList.join(", ")}
previous: ${previousList.join(", ")}
changes: ${changesList.join(", ")}
additions: ${additionsList.join(", ")}
removals: ${removalsList.join(", ")}
""";
  }
}

class KeyValueRecord<K, V> implements MapKeyValue<K, V> {
  final K key;
  V _previousValue, _currentValue;

  V get previousValue => _previousValue;
  V get currentValue => _currentValue;

  KeyValueRecord<K, V> _nextPrevious;
  KeyValueRecord<K, V> _next;
  KeyValueRecord<K, V> _nextAdded;
  KeyValueRecord<K, V> _nextRemoved, _prevRemoved;
  KeyValueRecord<K, V> _nextChanged;

  KeyValueRecord(this.key);

  String toString() => _previousValue == _currentValue
        ? "$key"
        : '$key[$_previousValue -> $_currentValue]';
}

class _CollectionChangeRecord<V> implements CollectionChangeRecord<V> {
  Iterable _iterable;
  int _length;

  /// Keeps track of moved items.
  DuplicateMap _movedItems = new DuplicateMap();

  /// Keeps track of removed items.
  DuplicateMap _removedItems = new DuplicateMap();

  ItemRecord<V> _previousItHead;
  ItemRecord<V> _itHead, _itTail;
  ItemRecord<V> _additionsHead, _additionsTail;
  ItemRecord<V> _movesHead, _movesTail;
  ItemRecord<V> _removalsHead, _removalsTail;

  void _revertToPreviousState() {
    if (!isDirty) return;

    _movedItems.clear();
    ItemRecord<V> prev;
    int i = 0;

    for (ItemRecord<V> record = _itHead = _previousItHead;
         record != null;
         prev = record, record = record._nextPrevious, i++) {
      record.currentIndex = record.previousIndex = i;
      record._prev = prev;
      if (prev != null) prev._next = prev._nextPrevious = record;
      _movedItems.put(record);
    }

    prev._next = null;
    _itTail = prev;
    _undoDeltas();
  }

  void forEachItem(void f(CollectionChangeItem<V> item)) {
    for (var r = _itHead; r != null; r = r._next) {
      f(r);
    }
  }

  void forEachPreviousItem(void f(CollectionChangeItem<V> previousItem)) {
    for (var r = _previousItHead; r != null; r = r._nextPrevious) {
      f(r);
    }
  }

  void forEachAddition(void f(CollectionChangeItem<V> addition)){
    for (var r = _additionsHead; r != null; r = r._nextAdded) {
      f(r);
    }
  }

  void forEachMove(void f(CollectionChangeItem<V> change)) {
    for (var r = _movesHead; r != null; r = r._nextMoved) {
      f(r);
    }
  }

  void forEachRemoval(void f(CollectionChangeItem<V> removal)){
    for (var r = _removalsHead; r != null; r = r._nextRemoved) {
      f(r);
    }
  }

  Iterable get iterable => _iterable;
  int get length => _length;

  bool _check(Iterable collection) {
    _reset();
    if (collection is UnmodifiableListView && identical(_iterable, collection)) {
      // Short circuit and assume that the list has not been modified.
      return false;
    }

    ItemRecord<V> record = _itHead;
    bool maybeDirty = false;

    if (collection is List) {
      List list = collection;
      _length = list.length;
      for (int index = 0; index < _length; index++) {
        var item = list[index];
        if (record == null || !identical(item, record.item)) {
          record = mismatch(record, item, index);
          maybeDirty = true;
        } else if (maybeDirty) {
          // TODO(misko): can we limit this to duplicates only?
          record = verifyReinsertion(record, item, index);
        }
        record = record._next;
      }
    } else {
      int index = 0;
      for (var item in collection) {
        if (record == null || !identical(item, record.item)) {
          record = mismatch(record, item, index);
          maybeDirty = true;
        } else if (maybeDirty) {
          // TODO(misko): can we limit this to duplicates only?
          record = verifyReinsertion(record, item, index);
        }
        record = record._next;
        index++;
      }
      _length = index;
    }

    _truncate(record);
    _iterable = collection;
    return isDirty;
  }

  /**
   * Reset the state of the change objects to show no changes. This means set
   * previousKey to currentKey, and clear all of the queues (additions, moves,
   * removals).
   */
  void _reset() {
    if (isDirty) {
      // Record the state of the collection for a possible _revertToPreviousState()
      for (ItemRecord<V> record = _previousItHead = _itHead;
           record != null;
           record = record._next) {
        record._nextPrevious = record._next;
      }
      _undoDeltas();
    }
  }

  void _undoDeltas() {
    ItemRecord<V> record;

    record = _additionsHead;
    while (record != null) {
      record.previousIndex = record.currentIndex;
      record = record._nextAdded;
    }
    _additionsHead = _additionsTail = null;

    record = _movesHead;
    while (record != null) {
      record.previousIndex = record.currentIndex;
      var nextRecord = record._nextMoved;
      assert((record._nextMoved = null) == null);
      record = nextRecord;
    }
    _movesHead = _movesTail = null;
    _removalsHead = _removalsTail = null;
    assert(isDirty == false);
  }

  /**
   * A [_CollectionChangeRecord] is considered dirty if it has additions, moves
   * or removals.
   */
  bool get isDirty => _additionsHead != null ||
                      _movesHead != null ||
                      _removalsHead != null;

  /**
   * This is the core function which handles differences between collections.
   *
   * - [record] is the record which we saw at this position last time. If
   *   [:null:] then it is a new item.
   * - [item] is the current item in the collection
   * - [index] is the position of the item in the collection
   */
  ItemRecord<V> mismatch(ItemRecord<V> record, item, int index) {
    if (record != null) {
      if (item is String && record.item is String && record.item == item) {
        // this is false change in strings we need to recover, and pretend it is
        // the same. We save the value so that next time identity can pass
        return record..item = item;
      }

      if (item is num && (item as num).isNaN && record.item is num && (record.item as num).isNaN){
        // we need this for JavaScript since in JS NaN !== NaN.
        return record;
      }
    }

    // find the previous record so that we know where to insert after.
    ItemRecord<V> prev = record == null ? _itTail : record._prev;

    // Remove the record from the collection since we know it does not match the
    // item.
    if (record != null) _collection_remove(record);
    // Attempt to see if we have seen the item before.
    record = _movedItems.get(item, index);
    if (record != null) {
      // We have seen this before, we need to move it forward in the collection.
      _collection_moveAfter(record, prev, index);
    } else {
      // Never seen it, check evicted list.
      record = _removedItems.get(item);
      if (record != null) {
        // It is an item which we have earlier evict it, reinsert it back into
        // the list.
        _collection_reinsertAfter(record, prev, index);
      } else {
        // It is a new item add it.
        record = _collection_addAfter(new ItemRecord<V>(item), prev, index);
      }
    }
    return record;
  }

  /**
   * This check is only needed if an array contains duplicates. (Short circuit
   * of nothing dirty)
   *
   * Use case: `[a, a]` => `[b, a, a]`
   *
   * If we did not have this check then the insertion of `b` would:
   *   1) evict first `a`
   *   2) insert `b` at `0` index.
   *   3) leave `a` at index `1` as is. <-- this is wrong!
   *   3) reinsert `a` at index 2. <-- this is wrong!
   *
   * The correct behavior is:
   *   1) evict first `a`
   *   2) insert `b` at `0` index.
   *   3) reinsert `a` at index 1.
   *   3) move `a` at from `1` to `2`.
   *
   *
   * Double check that we have not evicted a duplicate item. We need to check if
   * the item type may have already been removed:
   * The insertion of b will evict the first 'a'. If we don't reinsert it now it
   * will be reinserted at the end. Which will show up as the two 'a's switching
   * position. This is incorrect, since a better way to think of it is as insert
   * of 'b' rather then switch 'a' with 'b' and then add 'a' at the end.
   */
  ItemRecord<V> verifyReinsertion(ItemRecord record, dynamic item,
                               int index) {
    ItemRecord<V> reinsertRecord = _removedItems.get(item);
    if (reinsertRecord != null) {
      record = _collection_reinsertAfter(reinsertRecord, record._prev, index);
    } else if (record.currentIndex != index) {
      record.currentIndex = index;
      _moves_add(record);
    }
    return record;
  }

  /**
   * Get rid of any excess [ItemRecord]s from the previous collection
   *
   * - [record] The first excess [ItemRecord].
   */
  void _truncate(ItemRecord<V> record) {
    // Anything after that needs to be removed;
    while (record != null) {
      ItemRecord<V> nextRecord = record._next;
      _removals_add(_collection_unlink(record));
      record = nextRecord;
    }
    _removedItems.clear();

    if (_additionsTail != null) _additionsTail._nextAdded = null;
    if (_movesTail != null) _movesTail._nextMoved = null;
    if (_itTail != null) _itTail._next = null;
    if (_removalsTail != null) _removalsTail._nextRemoved = null;
  }

  ItemRecord<V> _collection_reinsertAfter(ItemRecord<V> record,
                                          ItemRecord<V> insertPrev,
                                          int index) {
    _removedItems.remove(record);
    var prev = record._prevRemoved;
    var next = record._nextRemoved;

    assert((record._prevRemoved = null) == null);
    assert((record._nextRemoved = null) == null);

    if (prev == null) {
      _removalsHead = next;
    } else {
      prev._nextRemoved = next;
    }
    if (next == null) {
      _removalsTail = prev;
    } else {
      next._prevRemoved = prev;
    }

    _collection_insertAfter(record, insertPrev, index);
    _moves_add(record);
    return record;
  }

  ItemRecord<V> _collection_moveAfter(ItemRecord<V> record,
                                      ItemRecord<V> prev,
                                      int index) {
    _collection_unlink(record);
    _collection_insertAfter(record, prev, index);
    _moves_add(record);
    return record;
  }

  ItemRecord<V> _collection_addAfter(ItemRecord<V> record,
                                     ItemRecord<V> prev,
                                     int index) {
    _collection_insertAfter(record, prev, index);

    if (_additionsTail == null) {
      assert(_additionsHead == null);
      _additionsTail = _additionsHead = record;
    } else {
      assert(_additionsTail._nextAdded == null);
      assert(record._nextAdded == null);
      _additionsTail = _additionsTail._nextAdded = record;
    }
    return record;
  }

  ItemRecord<V> _collection_insertAfter(ItemRecord<V> record,
                                        ItemRecord<V> prev,
                                        int index) {
    assert(record != prev);
    assert(record._next == null);
    assert(record._prev == null);

    ItemRecord<V> next = prev == null ? _itHead : prev._next;
    assert(next != record);
    assert(prev != record);
    record._next = next;
    record._prev = prev;
    if (next == null) {
      _itTail = record;
    } else {
      next._prev = record;
    }
    if (prev == null) {
      _itHead = record;
    } else {
      prev._next = record;
    }

    _movedItems.put(record);
    record.currentIndex = index;
    return record;
  }

  ItemRecord<V> _collection_remove(ItemRecord record) =>
      _removals_add(_collection_unlink(record));

  ItemRecord<V> _collection_unlink(ItemRecord record) {
    _movedItems.remove(record);

    var prev = record._prev;
    var next = record._next;

    assert((record._prev = null) == null);
    assert((record._next = null) == null);

    if (prev == null) {
      _itHead = next;
    } else {
      prev._next = next;
    }
    if (next == null) {
      _itTail = prev;
    } else {
      next._prev = prev;
    }

    return record;
  }

  ItemRecord<V> _moves_add(ItemRecord<V> record) {
    assert(record._nextMoved == null);
    if (_movesTail == null) {
      assert(_movesHead == null);
      _movesTail = _movesHead = record;
    } else {
      assert(_movesTail._nextMoved == null);
      _movesTail = _movesTail._nextMoved = record;
    }

    return record;
  }

  ItemRecord<V> _removals_add(ItemRecord<V> record) {
    record.currentIndex = null;
    _removedItems.put(record);

    if (_removalsTail == null) {
      assert(_removalsHead == null);
      _removalsTail = _removalsHead = record;
    } else {
      assert(_removalsTail._nextRemoved == null);
      assert(record._nextRemoved == null);
      record._prevRemoved = _removalsTail;
      _removalsTail = _removalsTail._nextRemoved = record;
    }
    return record;
  }

  String toString() {
    ItemRecord<V> r;

    var list = [];
    for (r = _itHead; r != null; r = r._next) {
      list.add(r);
    }

    var previous = [];
    for (r = _previousItHead; r != null; r = r._nextPrevious) {
      previous.add(r);
    }

    var additions = [];
    for (r = _additionsHead; r != null; r = r._nextAdded) {
      additions.add(r);
    }
    var moves = [];
    for (r = _movesHead; r != null; r = r._nextMoved) {
      moves.add(r);
    }

    var removals = [];
    for (r = _removalsHead; r != null; r = r._nextRemoved) {
      removals.add(r);
    }

    return """
collection: ${list.join(", ")}
previous: ${previous.join(", ")}
additions: ${additions.join(", ")}
moves: ${moves.join(", ")}
removals: ${removals.join(", ")}
""";
  }
}

class ItemRecord<V> extends CollectionChangeItem<V>  {
  int currentIndex;
  int previousIndex;
  V item;

  ItemRecord<V> _nextPrevious;
  ItemRecord<V> _prev, _next;
  ItemRecord<V> _prevDup, _nextDup;
  ItemRecord<V> _prevRemoved, _nextRemoved;
  ItemRecord<V> _nextAdded;
  ItemRecord<V> _nextMoved;

  ItemRecord(this.item);

  String toString() => previousIndex == currentIndex
      ? '$item'
      : '$item[$previousIndex -> $currentIndex]';
}

class _DuplicateItemRecordList {
  ItemRecord head, tail;

  /**
   * Add the [record] before the [previousRecord] in the list of duplicates or
   * at the end of the list when no [previousRecord] is specified.
   *
   * Note: by design all records in the list of duplicates hold the save value
   * in [record.item].
   */
  void add(ItemRecord record, ItemRecord previousRecord) {
    assert(previousRecord == null || previousRecord.item == record.item);
    if (head == null) {
      assert(previousRecord == null);
      head = tail = record;
      record._nextDup = null;
      record._prevDup = null;
    } else {
      assert(record.item == head.item);
      if (previousRecord == null) {
        tail._nextDup = record;
        record._prevDup = tail;
        record._nextDup = null;
        tail = record;
      } else {
        var prev = previousRecord._prevDup;
        var next = previousRecord;
        record._prevDup = prev;
        record._nextDup = next;
        if (prev == null) {
          head = record;
        } else {
          prev._nextDup = record;
        }
        next._prevDup = record;
      }
    }
  }

  ItemRecord get(key, int hideIndex) {
    ItemRecord record;
    for (record = head; record != null; record = record._nextDup) {
      if ((hideIndex == null || hideIndex < record.currentIndex) &&
          identical(record.item, key)) {
        return record;
      }
    }
    return record;
  }

  /**
   * Remove one [ItemRecord] from the list of duplicates.
   *
   * Returns whether when the list of duplicates is empty.
   */
  bool remove(ItemRecord record) {
    assert(() {
      // verify that the record being removed is someplace in the list.
      for (ItemRecord cursor = head; cursor != null; cursor = cursor._nextDup) {
        if (identical(cursor, record)) return true;
      }
      return false;
    });

    var prev = record._prevDup;
    var next = record._nextDup;
    if (prev == null) {
      head = next;
    } else {
      prev._nextDup = next;
    }
    if (next == null) {
      tail = prev;
    } else {
      next._prevDup = prev;
    }
    return head == null;
  }
}

/**
 * [DuplicateMap] maps [ItemRecord.value] to a list of [ItemRecord] having the
 * same value (duplicates).
 *
 * The list of duplicates is implemented by [_DuplicateItemRecordList].
 *
 */
class DuplicateMap {
  final map = <dynamic, _DuplicateItemRecordList>{};

  void put(ItemRecord record, [ItemRecord beforeRecord = null]) {
    map.putIfAbsent(record.item, () => new _DuplicateItemRecordList())
        .add(record, beforeRecord);
  }

  /**
   * Retrieve the `value` using [key]. Because the [ItemRecord] value maybe one
   * which we have already iterated over, we use the [hideIndex] to pretend it
   * is not there.
   *
   * Use case: `[a, b, c, a, a]` if we are at index `3` which is the second `a`
   * then asking if we have any more `a`s needs to return the last `a` not the
   * first or second.
   */
  ItemRecord get(key, [int hideIndex]) {
    _DuplicateItemRecordList recordList = map[key];
    return recordList == null ? null : recordList.get(key, hideIndex);
  }

  /**
   * Removes an [ItemRecord] from the list of duplicates.
   *
   * The list of duplicates also is removed from the map if it gets empty.
   */
  ItemRecord remove(ItemRecord record) {
    _DuplicateItemRecordList recordList = map[record.item];
    assert(recordList != null);
    if (recordList.remove(record)) map.remove(record.item);
    return record;
  }

  bool get isEmpty => map.isEmpty;

  void clear() {
    map.clear();
  }

  String toString() => "$runtimeType($map)";
}
