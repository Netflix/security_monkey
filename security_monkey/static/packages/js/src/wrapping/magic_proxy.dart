// Copyright (c) 2013, the Dart project authors.  Please see the AUTHORS file
// for details. All rights reserved. Use of this source code is governed by a
// BSD-style license that can be found in the LICENSE file.

part of js.wrapping;

/// base class to simplify declaration of [TypedProxy].
class MagicProxy extends TypedProxy {
  MagicProxy([Serializable<FunctionProxy> function, List args])
      : this.fromProxy(new Proxy.withArgList(
            function != null ? function : context.Object,
            args != null ? args : []));
  MagicProxy.fromProxy(Proxy proxy) : super.fromProxy(proxy);

  operator[](arg) => $unsafe[arg];
  operator[]=(key, value) => $unsafe[key] = value;

  @override noSuchMethod(Invocation invocation) =>
      $unsafe.noSuchMethod(invocation);
}
