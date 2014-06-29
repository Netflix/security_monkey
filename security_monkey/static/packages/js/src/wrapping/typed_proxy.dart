// Copyright (c) 2013, the Dart project authors.  Please see the AUTHORS file
// for details. All rights reserved. Use of this source code is governed by a
// BSD-style license that can be found in the LICENSE file.

part of js.wrapping;

/// base class to wrap a [Proxy] in a strong typed object.
class TypedProxy implements Serializable<Proxy> {
  final Proxy $unsafe;

  TypedProxy([Serializable<FunctionProxy> function, List args])
      : this.fromProxy(new Proxy.withArgList(
            function != null ? function : context.Object,
            args != null ? args : []));
  TypedProxy.fromProxy(this.$unsafe);

  @override dynamic toJs() => $unsafe;
}
