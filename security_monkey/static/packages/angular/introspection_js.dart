library angular.introspection_expando;

import 'dart:html' as dom;
import 'dart:js' as js;

import 'package:di/di.dart';
import 'package:angular/introspection.dart';
import 'package:angular/core/module_internal.dart';
import 'package:angular/core_dom/module_internal.dart';

/**
 * A global write only variable which keeps track of objects attached to the
 * elements. This is useful for debugging AngularDart application from the
 * browser's REPL.
 */
var elementExpando = new Expando('element');

void publishToJavaScript() {
  js.context
    ..['ngProbe'] = new js.JsFunction.withThis((_, nodeOrSelector) =>
        _jsProbe(ngProbe(nodeOrSelector)))
    ..['ngInjector'] = new js.JsFunction.withThis((_, nodeOrSelector) =>
        _jsInjector(ngInjector(nodeOrSelector)))
    ..['ngScope'] = new js.JsFunction.withThis((_, nodeOrSelector) =>
        _jsScope(ngScope(nodeOrSelector), ngProbe(nodeOrSelector).injector.get(ScopeStatsConfig)))
    ..['ngQuery'] = new js.JsFunction.withThis((_, dom.Node node, String selector, [String containsText]) =>
        new js.JsArray.from(ngQuery(node, selector, containsText)));
}

js.JsObject _jsProbe(ElementProbe probe) {
  return new js.JsObject.jsify({
      "element": probe.element,
      "injector": _jsInjector(probe.injector),
      "scope": _jsScope(probe.scope, probe.injector.get(ScopeStatsConfig)),
      "directives": probe.directives.map((directive) => _jsDirective(directive))
  })..['_dart_'] = probe;
}

js.JsObject _jsInjector(Injector injector) =>
    new js.JsObject.jsify({"get": injector.get})..['_dart_'] = injector;

js.JsObject _jsScope(Scope scope, ScopeStatsConfig config) {
  return new js.JsObject.jsify({
      "apply": scope.apply,
      "broadcast": scope.broadcast,
      "context": scope.context,
      "destroy": scope.destroy,
      "digest": scope.rootScope.digest,
      "emit": scope.emit,
      "flush": scope.rootScope.flush,
      "get": (name) => scope.context[name],
      "isAttached": scope.isAttached,
      "isDestroyed": scope.isDestroyed,
      "set": (name, value) => scope.context[name] = value,
      "scopeStatsEnable": () => config.emit = true,
      "scopeStatsDisable": () => config.emit = false
  })..['_dart_'] = scope;
}

_jsDirective(directive) => directive;
