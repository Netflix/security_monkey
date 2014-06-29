// Copyright (c) 2013, the Dart project authors.  Please see the AUTHORS file
// for details. All rights reserved. Use of this source code is governed by a
// BSD-style license that can be found in the LICENSE file.

/**
 * The js.dart library provides simple JavaScript invocation from Dart that
 * works on both Dartium and on other modern browsers via Dart2JS.
 *
 * It provides a model based on scoped [Proxy] objects.  Proxies give Dart
 * code access to JavaScript objects, fields, and functions as well as the
 * ability to pass Dart objects and functions to JavaScript functions.  Scopes
 * enable developers to use proxies without memory leaks - a common challenge
 * with cross-runtime interoperation.
 *
 * The top-level [context] getter provides a [Proxy] to the global JavaScript
 * context for the page your Dart code is running on. In the following example:
 *
 *     import 'package:js/js.dart' as js;
 *
 *     void main() {
 *       js.context.alert('Hello from Dart via JavaScript');
 *     }
 *
 * js.context.alert creates a proxy to the top-level alert function in
 * JavaScript.  It is invoked from Dart as a regular function that forwards to
 * the underlying JavaScript one. By default, proxies are released when
 * the currently executing event completes, e.g., when main is completes
 * in this example.
 *
 * The library also enables JavaScript proxies to Dart objects and functions.
 * For example, the following Dart code:
 *
 *     js.context.dartCallback = (x) => print(x*2);
 *
 * defines a top-level JavaScript function 'dartCallback' that is a proxy to
 * the corresponding Dart function.
 *
 * Note, parameters and return values are intuitively passed by value for
 * primitives and by reference for non-primitives. In the latter case, the
 * references are automatically wrapped and unwrapped as proxies by the library.
 *
 * This library also allows construction of JavaScripts objects given a [Proxy]
 * to a corresponding JavaScript constructor. For example, if the following
 * JavaScript is loaded on the page:
 *
 *     function Foo(x) {
 *       this.x = x;
 *     }
 *
 *     Foo.prototype.add = function(other) {
 *       return new Foo(this.x + other.x);
 *     }
 *
 * then, the following Dart:
 *
 *     var foo = new js.Proxy(js.context.Foo, 42);
 *     var foo2 = foo.add(foo);
 *     print(foo2.x);
 *
 * will construct a JavaScript Foo object with the parameter 42, invoke its
 * add method, and return a [Proxy] to a new Foo object whose x field is 84.
 *
 * See [samples](http://dart-lang.github.com/js-interop/example) for more
 * examples of usage.
 *
 * See this [article](http://www.dartlang.org/articles/js-dart-interop) for
 * more detailed discussion.
 */

library js;

import 'dart:js' as js;
import 'dart:mirrors';

/**
 * A proxy on the global JavaScript context for this page.
 */
final Proxy context = new Proxy._(js.context);

/**
 * Check if [proxy] is instance of [type].
 */
bool instanceof(Serializable<Proxy> proxy, Serializable<FunctionProxy> type) =>
    proxy.toJs()._jsObject.instanceof(type.toJs()._jsObject);

/**
 * Check if [proxy] has a [name] property.
 */
bool hasProperty(Serializable<Proxy> proxy, String name) =>
    proxy.toJs()._jsObject.hasProperty(name);

/**
 * Delete the [name] property of [proxy].
 */
void deleteProperty(Serializable<Proxy> proxy, String name) {
  proxy.toJs()._jsObject.deleteProperty(name);
}

/**
 * Converts a Dart map [data] to a JavaScript map and return a [Proxy] to it.
 */
Proxy map(Map data) => new Proxy._json(data);

/**
 * Converts a Dart [Iterable] to a JavaScript array and return a [Proxy] to it.
 */
Proxy array(Iterable data) => new Proxy._json(data);

// Detect unspecified arguments.
class _Undefined {
  const _Undefined();
}

const _undefined = const _Undefined();

List _pruneUndefined(arg1, arg2, arg3, arg4, arg5, arg6) {
  // This assumes no argument
  final args = [arg1, arg2, arg3, arg4, arg5, arg6];
  final index = args.indexOf(_undefined);
  if (index < 0) return args;
  return args.sublist(0, index);
}

/**
 * Proxies to JavaScript objects.
 */
@proxy
class Proxy<T extends Proxy> implements Serializable<T> {
  final js.JsObject _jsObject;

  Proxy._(this._jsObject);

  /**
   * Constructs a [Proxy] that proxies a native Dart object; _for expert use
   * only_.
   *
   * Use this constructor only if you wish to get access to JavaScript
   * properties attached to a browser host object, such as a Node or Blob, that
   * is normally automatically converted into a native Dart object.
   *
   * An exception will be thrown if [object] either is `null` or has the type
   * `bool`, `num`, or `String`.
   */
  Proxy.fromBrowserObject(o) : this._(new js.JsObject.fromBrowserObject(o));

  /**
  * Constructs a [Proxy] to a new JavaScript object by invoking a (proxy to a)
  * JavaScript [constructor]. The arguments should be either
  * primitive values, DOM elements, or Proxies.
  */
  factory Proxy(Serializable<FunctionProxy> constructor,
      [arg1 = _undefined,
       arg2 = _undefined,
       arg3 = _undefined,
       arg4 = _undefined,
       arg5 = _undefined,
       arg6 = _undefined]) {
      var arguments = _pruneUndefined(arg1, arg2, arg3, arg4, arg5, arg6);
      return new Proxy.withArgList(constructor, arguments);
  }

  /**
  * Constructs a [Proxy] to a new JavaScript object by invoking a (proxy to a)
  * JavaScript [constructor]. The [arguments] list should contain either
  * primitive values, DOM elements, or Proxies.
  */
  factory Proxy.withArgList(Serializable<FunctionProxy> constructor,
      List arguments) => new Proxy._(new js.JsObject(
          constructor.toJs()._jsObject, arguments.map(_serialize).toList()));

  /**
  * Constructs a [Proxy] to a new JavaScript map or list created defined via
  * Dart map or list.
  */
  factory Proxy._json(data) =>
      new Proxy._(new js.JsObject.jsify(_serializeDataTree(data)));

  static _serializeDataTree(data) {
    if (data is Map) {
      final map = new Map();
      for (var key in data.keys) {
        map[key] = _serializeDataTree(data[key]);
      }
      return map;
    } else if (data is Iterable) {
      return data.map(_serializeDataTree).toList();
    } else {
      return _serialize(data);
    }
  }

  Proxy toJs() => this;

  // Resolve whether this is needed.
  operator[](arg) => _deserialize(_jsObject[arg], thisArg: this);

  // Resolve whether this is needed.
  operator[]=(key, value) => _jsObject[key] = _serialize(value);

  int get hashCode => _jsObject.hashCode;

  // Test if this is equivalent to another Proxy. This essentially
  // maps to JavaScript's == operator.
  operator==(other) => _jsObject == _serialize(other);

  String toString() => _jsObject.toString();

  // Forward member accesses to the backing JavaScript object.
  noSuchMethod(Invocation invocation) {
    String member = MirrorSystem.getName(invocation.memberName);
    // If trying to access a JavaScript field/variable that starts with
    // _ (underscore), Dart treats it a library private and member name
    // it suffixed with '@internalLibraryIdentifier' which we have to
    // strip before sending over to the JS side.
    if (member.indexOf('@') != -1) {
      member = member.substring(0, member.indexOf('@'));
    }
    if (invocation.isGetter) {
      if (_jsObject.hasProperty(member)) {
        return _deserialize(_jsObject[member], thisArg: this);
      } else {
        super.noSuchMethod(invocation);
      }
    } else if (invocation.isSetter) {
      if (member.endsWith('=')) {
        member = member.substring(0, member.length - 1);
      }
      _jsObject[member] = _serialize(invocation.positionalArguments[0]);
      return null;
    } else {
      return _deserialize(_jsObject.callMethod(member,
          invocation.positionalArguments.map(_serialize).toList()),
          thisArg: this);
    }
  }
}

class _CallbackFunction implements Function {
  final Function f;
  final bool withThis;

  _CallbackFunction(this.f, {this.withThis});

  call() => throw new StateError('There should always been at least 1 parameter'
      '(js this).');

  noSuchMethod(Invocation invocation) {
    final args = invocation.positionalArguments.skip(
        withThis != null && withThis ? 0 : 1);
    return _serialize(Function.apply(f,
        args.map((e) => _deserialize(e)).toList()));
  }
}

/// A [Proxy] subtype to JavaScript functions.
class FunctionProxy extends Proxy<FunctionProxy> implements Function {
  final js.JsFunction _jsFunction;
  final _thisArg;

  FunctionProxy._(js.JsFunction jsFunction, {thisArg}) :
      this._jsFunction = jsFunction,
      this._thisArg = thisArg,
      super._(jsFunction);

  factory FunctionProxy(Function f) => new FunctionProxy._(
      new js.JsFunction.withThis(new _CallbackFunction(f)));

  factory FunctionProxy.withThis(Function f) => new FunctionProxy._(
      new js.JsFunction.withThis(new _CallbackFunction(f, withThis: true)));

  // We need to implement call() to satisfy the Function "interface"
  // This handles the no-arg case, noSuchMethod handles the rest.
  call() => _deserialize(_jsFunction.apply([], thisArg: _serialize(_thisArg)),
      thisArg: this);

  noSuchMethod(Invocation invocation) {
    String member = MirrorSystem.getName(invocation.memberName);
    // If trying to access a JavaScript field/variable that starts with
    // _ (underscore), Dart treats it a library private and member name
    // it suffixed with '@internalLibraryIdentifier' which we have to
    // strip before sending over to the JS side.
    if (member.indexOf('@') != -1) {
      member = member.substring(0, member.indexOf('@'));
    }
    if (member == 'call') {
      // A 'call' (probably) means that this proxy was invoked directly
      // as if it was a function. Map this to JS function application.
      return _deserialize(_jsFunction.apply(
          invocation.positionalArguments.map(_serialize).toList(),
          thisArg: _serialize(_thisArg)), thisArg: this);
    }
    return super.noSuchMethod(invocation);
  }
}

/// Marker class used to indicate it is serializable to js. If a class is a
/// [Serializable] the "toJs" method will be called and the result will be used
/// as value.
abstract class Serializable<T> {
  T toJs();
}

_serialize(var o) {
  if (o == null) {
    return null;
  } else if (o is Proxy) {
    return o._jsObject;
  } else if (o is Serializable) {
    return _serialize(o.toJs());
  } else if (o is Function) {
    return _serialize(new FunctionProxy(o));
  } else {
    return o;
  }
}

_deserialize(var o, {thisArg}) {
  if (o == null) {
    return null;
  } else if (o is js.JsFunction) {
    return new FunctionProxy._(o, thisArg: thisArg);
  } else if (o is js.JsObject) {
    return new Proxy._(o);
  } else {
    return o;
  }
}
