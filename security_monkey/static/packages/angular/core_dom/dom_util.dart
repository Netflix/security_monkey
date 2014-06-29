library angular.dom.util;

import 'dart:html' as dom;

Iterable<dom.Element> getElements(Iterable<dom.Node> nodes) =>
    nodes.where((el) => el.nodeType == dom.Node.ELEMENT_NODE);

void domRemove(List<dom.Node> nodes) {
  // Not every element is sequential if the list of nodes only
  // includes the elements. Removing a view also includes
  // removing non-element nodes in-between.
  for (var j = 0; j < nodes.length; j++) {
    dom.Node current = nodes[j];
    dom.Node next = j + 1 < nodes.length ? nodes[j + 1] : null;

    while (next != null && current.nextNode != next) {
      current.nextNode.remove();
    }
    nodes[j].remove();
  }
}

void domInsert(Iterable<dom.Node> nodes, dom.Node parent,
                { dom.Node insertBefore }) {
  parent.insertAllBefore(nodes, insertBefore);
}

void domMove(Iterable<dom.Node> nodes, dom.Node parent,
              { dom.Node insertBefore }) {
  nodes.forEach((n) {
    if (n.parentNode == null) n.remove();
    parent.insertBefore(n, insertBefore);
  });
}

List<dom.Node> allNodesBetween(List<dom.Node> nodes) {
  var result = [];
  // Not every element is sequential if the list of nodes only
  // includes the elements. Removing a view also includes
  // removing non-element nodes in-between.
  for (var j = 0; j < nodes.length; j++) {
    dom.Node current = nodes[j];
    dom.Node next = j + 1 < nodes.length ? nodes[j + 1] : null;

    while (next != null && current.nextNode != next) {
      result.add(current.nextNode);
      current = current.nextNode;
    }
    result.add(nodes[j]);
  }
  return result;
}

/**
 * Computes and returns the longest css transition or keyframe animation from
 * a computed style in milliseconds.
 */
num computeLongestTransition(style) {
  double longestTransitionSeconds = 0.0;

  if (style.transitionDuration.length > 0) {
    // Parse transitions
    List<num> durations = _parseDurationList(style.transitionDuration)
        .toList(growable: false);
    List<num> delays = _parseDurationList(style.transitionDelay)
        .toList(growable: false);

    assert(durations.length == delays.length);

    for (int i = 0; i < durations.length; i++) {
      var total = _computeTotalDurationSeconds(delays[i], durations[i]);
      if (total > longestTransitionSeconds) longestTransitionSeconds = total;
    }
  }

  if (style.animationDuration.length > 0) {
    // Parse and add animation duration properties.
    List<num> animationDurations =
        _parseDurationList(style.animationDuration).toList(growable: false);
    // Note that animation iteration count only affects duration NOT delay.
    List<num> animationDelays =
        _parseDurationList(style.animationDelay).toList(growable: false);

    List<num> iterationCounts = _parseIterationCounts(
        style.animationIterationCount).toList(growable: false);

    assert(animationDurations.length == animationDelays.length);

    for (int i = 0; i < animationDurations.length; i++) {
      var total = _computeTotalDurationSeconds(
          animationDelays[i], animationDurations[i],
          iterations: iterationCounts[i]);
      if (total > longestTransitionSeconds) longestTransitionSeconds = total;
    }
  }

  // transition time in milliseconds.
  return longestTransitionSeconds * 1000;
}

Iterable<num> _parseIterationCounts(String iterationCounts) => iterationCounts
    .split(", ")
    .map((x) => x == "infinite" ? -1 : double.parse(x));

/// This expects a string in the form "0s, 3.234s, 10s" and will return a list
/// of doubles of (0, 3.234, 10).
Iterable<num> _parseDurationList(String durations) => durations
    .split(", ")
    .map((x) => _parseCssDuration(x));

/// This expects a string in the form of '0.234s' or '4s' and will return
/// a parsed double.
num _parseCssDuration(String cssDuration) =>
    double.parse(cssDuration.substring(0, cssDuration.length - 1));

num _computeTotalDurationSeconds(num delay, num duration,
                                 {num iterations: 1}) {
  if (iterations == 0) return 0.0;
  if (iterations < 0) iterations = 1; // infinite

  return (duration * iterations) + delay;
}
