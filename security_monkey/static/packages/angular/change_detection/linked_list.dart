part of angular.watch_group;


class _LinkedListItem<I extends _LinkedListItem> {
  I _previous, _next;
}

class _LinkedList<L extends _LinkedListItem> {
  L _head, _tail;

  static _Handler _add(_Handler list, _LinkedListItem item) {
    assert(item._next     == null);
    assert(item._previous == null);
    if (list._tail == null) {
      list._head = list._tail = item;
    } else {
      item._previous = list._tail;
      list._tail._next = item;
      list._tail = item;
    }
    return item;
  }

  static bool _isEmpty(_Handler list) => list._head == null;

  static void _remove(_Handler list, _Handler item) {
    var previous = item._previous;
    var next = item._next;

    if (previous == null) list._head = next;     else previous._next = next;
    if (next == null)     list._tail = previous; else next._previous = previous;
  }
}

class _ArgHandlerList {
  _ArgHandler _argHandlerHead, _argHandlerTail;

  static _Handler _add(_ArgHandlerList list, _ArgHandler item) {
    assert(item._nextArgHandler     == null);
    assert(item._previousArgHandler == null);
    if (list._argHandlerTail == null) {
      list._argHandlerHead = list._argHandlerTail = item;
    } else {
      item._previousArgHandler = list._argHandlerTail;
      list._argHandlerTail._nextArgHandler = item;
      list._argHandlerTail = item;
    }
    return item;
  }

  static bool _isEmpty(_InvokeHandler list) => list._argHandlerHead == null;

  static void _remove(_InvokeHandler list, _ArgHandler item) {
    var previous = item._previousArgHandler;
    var next = item._nextArgHandler;

    if (previous == null) list._argHandlerHead = next;     else previous._nextArgHandler = next;
    if (next == null)     list._argHandlerTail = previous; else next._previousArgHandler = previous;
  }
}

class _WatchList {
  Watch _watchHead, _watchTail;

  static Watch _add(_WatchList list, Watch item) {
    assert(item._nextWatch     == null);
    assert(item._previousWatch == null);
    if (list._watchTail == null) {
      list._watchHead = list._watchTail = item;
    } else {
      item._previousWatch = list._watchTail;
      list._watchTail._nextWatch = item;
      list._watchTail = item;
    }
    return item;
  }

  static bool _isEmpty(_Handler list) => list._watchHead == null;

  static void _remove(_Handler list, Watch item) {
    var previous = item._previousWatch;
    var next = item._nextWatch;

    if (previous == null) list._watchHead = next;     else previous._nextWatch = next;
    if (next == null)     list._watchTail = previous; else next._previousWatch = previous;
  }
}

abstract class _EvalWatchList {
  _EvalWatchRecord _evalWatchHead, _evalWatchTail;
  _EvalWatchRecord get _marker;

  static _EvalWatchRecord _add(_EvalWatchList list, _EvalWatchRecord item) {
    assert(item._nextEvalWatch     == null);
    assert(item._prevEvalWatch == null);
    var prev = list._evalWatchTail;
    var next = prev._nextEvalWatch;

    if (prev == list._marker) {
      list._evalWatchHead = list._evalWatchTail = item;
      prev = prev._prevEvalWatch;
      list._marker._prevEvalWatch = null;
      list._marker._nextEvalWatch = null;
    }
    item._nextEvalWatch = next;
    item._prevEvalWatch = prev;

    if (prev != null) prev._nextEvalWatch = item;
    if (next != null) next._prevEvalWatch = item;

    return list._evalWatchTail = item;
  }

  static bool _isEmpty(_EvalWatchList list) => list._evalWatchHead == null;

  static void _remove(_EvalWatchList list, _EvalWatchRecord item) {
    assert(item.watchGrp == list);
    var prev = item._prevEvalWatch;
    var next = item._nextEvalWatch;

    if (list._evalWatchHead == list._evalWatchTail) {
      list._evalWatchHead = list._evalWatchTail = list._marker;
      list._marker
          .._nextEvalWatch = next
          .._prevEvalWatch = prev;
      if (prev != null) prev._nextEvalWatch = list._marker;
      if (next != null) next._prevEvalWatch = list._marker;
    } else {
      if (item == list._evalWatchHead) list._evalWatchHead = next;
      if (item == list._evalWatchTail) list._evalWatchTail = prev;
      if (prev != null) prev._nextEvalWatch = next;
      if (next != null) next._prevEvalWatch = prev;
    }
  }
}

class _WatchGroupList {
  WatchGroup _watchGroupHead, _watchGroupTail;

  static WatchGroup _add(_WatchGroupList list, WatchGroup item) {
    assert(item._nextWatchGroup     == null);
    assert(item._prevWatchGroup == null);
    if (list._watchGroupTail == null) {
      list._watchGroupHead = list._watchGroupTail = item;
    } else {
      item._prevWatchGroup = list._watchGroupTail;
      list._watchGroupTail._nextWatchGroup = item;
      list._watchGroupTail = item;
    }
    return item;
  }

  static bool _isEmpty(_WatchGroupList list) => list._watchGroupHead == null;

  static void _remove(_WatchGroupList list, WatchGroup item) {
    var previous = item._prevWatchGroup;
    var next = item._nextWatchGroup;

    if (previous == null) list._watchGroupHead = next;     else previous._nextWatchGroup = next;
    if (next == null)     list._watchGroupTail = previous; else next._prevWatchGroup = previous;
  }
}
