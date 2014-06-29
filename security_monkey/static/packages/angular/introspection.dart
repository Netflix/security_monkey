/**
* Introspection of Elements for debugging and tests.
*/
library angular.introspection;

import 'dart:html' as dom;
import 'package:di/di.dart';
import 'package:angular/introspection_js.dart';
import 'package:angular/core/module_internal.dart';
import 'package:angular/core_dom/module_internal.dart';

/**
 * Return the [ElementProbe] object for the closest [Element] in the hierarchy.
 *
 * The node parameter could be:
 * * a [dom.Node],
 * * a CSS selector for this node.
 *
 * **NOTE:** This global method is here to make it easier to debug Angular
 * application from the browser's REPL, unit or end-to-end tests. The
 * function is not intended to be called from Angular application.
 */
ElementProbe ngProbe(nodeOrSelector) {
  var errorMsg;
  var node;
  if (nodeOrSelector == null) throw "ngProbe called without node";
  if (nodeOrSelector is String) {
    var nodes = ngQuery(dom.document, nodeOrSelector);
    if (nodes.isNotEmpty) node = nodes.first;
    errorMsg = "Could not find a probe for the selector '$nodeOrSelector' nor its parents";
  } else {
    node = nodeOrSelector;
    errorMsg = "Could not find a probe for the node '$node' nor its parents";
  }
  while (node != null) {
    var probe = elementExpando[node];
    if (probe != null) return probe;
    node = node.parent;
  }
  throw errorMsg;
}

/**
 * Return the [Injector] associated with a current [Element].
 *
 * **NOTE**: This global method is here to make it easier to debug Angular
 * application from the browser's REPL, unit or end-to-end tests. The function
 * is not intended to be called from Angular application.
 */
Injector ngInjector(nodeOrSelector) => ngProbe(nodeOrSelector).injector;


/**
 * Return the [Scope] associated with a current [Element].
 *
 * **NOTE**: This global method is here to make it easier to debug Angular
 * application from the browser's REPL, unit or end-to-end tests. The function
 * is not intended to be called from Angular application.
 */
Scope ngScope(nodeOrSelector) => ngProbe(nodeOrSelector).scope;


List<dom.Element> ngQuery(dom.Node element, String selector,
                          [String containsText]) {
  var list = [];
  var children = [element];
  if ((element is dom.Element) && element.shadowRoot != null) {
    children.add(element.shadowRoot);
  }
  while (!children.isEmpty) {
    var child = children.removeAt(0);
    child.querySelectorAll(selector).forEach((e) {
      if (containsText == null || e.text.contains(containsText)) list.add(e);
    });
    child.querySelectorAll('*').forEach((e) {
      if (e.shadowRoot != null) children.add(e.shadowRoot);
    });
  }
  return list;
}

/**
 * Return a List of directives associated with a current [Element].
 *
 * **NOTE**: This global method is here to make it easier to debug Angular
 * application from the browser's REPL, unit or end-to-end tests. The function
 * is not intended to be called from Angular application.
 */
List<Object> ngDirectives(nodeOrSelector) => ngProbe(nodeOrSelector).directives;

