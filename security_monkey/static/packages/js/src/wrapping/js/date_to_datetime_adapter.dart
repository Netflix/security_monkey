// Copyright (c) 2013, the Dart project authors.  Please see the AUTHORS file
// for details. All rights reserved. Use of this source code is governed by a
// BSD-style license that can be found in the LICENSE file.

part of js.wrapping;

/// Adapter to handle a js date as a dart [DateTime].
class JsDateToDateTimeAdapter extends TypedProxy implements DateTime {

  /// Like [JsDateToDateTimeAdapter.fromProxy] but with `null` handling for
  /// [proxy].
  static JsDateToDateTimeAdapter cast(Proxy proxy) =>
      mapNotNull(proxy, (proxy) =>
          new JsDateToDateTimeAdapter.fromProxy(proxy));

  /// Create a new adapter from a dart [dateTime].
  JsDateToDateTimeAdapter(DateTime dateTime) :
      super(context.Date, [dateTime.millisecondsSinceEpoch]);

  /// Create a new adapter from a [proxy] of a Js Date object.
  JsDateToDateTimeAdapter.fromProxy(Proxy proxy) : super.fromProxy(proxy);

  // from Comparable
  @override int compareTo(DateTime other) => _asDateTime().compareTo(other);

  // from Date
  @override bool operator ==(DateTime other) => _asDateTime() == other;
  @override bool isBefore(DateTime other) => _asDateTime().isBefore(other);
  @override bool isAfter(DateTime other) => _asDateTime().isAfter(other);
  @override bool isAtSameMomentAs(DateTime other) =>
      _asDateTime().isAtSameMomentAs(other);
  @override DateTime toLocal() => _asDateTime().toLocal();
  @override DateTime toUtc() => _asDateTime().toUtc();
  @override String get timeZoneName => _asDateTime().timeZoneName;
  @override Duration get timeZoneOffset => _asDateTime().timeZoneOffset;
  @override int get year => _asDateTime().year;
  @override int get month => _asDateTime().month;
  @override int get day => _asDateTime().day;
  @override int get hour => _asDateTime().hour;
  @override int get minute => _asDateTime().minute;
  @override int get second => _asDateTime().second;
  @override int get millisecond => _asDateTime().millisecond;
  @override int get weekday => _asDateTime().weekday;
  @override int get millisecondsSinceEpoch =>
      _asDateTime().millisecondsSinceEpoch;
  @override void set millisecondsSinceEpoch(v) => throw "final";
  @override bool get isUtc => _asDateTime().isUtc;
  @override void set isUtc(v) => throw "final";
  @override String toString() => _asDateTime().toString();
  @override DateTime add(Duration duration) => _asDateTime().add(duration);
  @override DateTime subtract(Duration duration) =>
      _asDateTime().subtract(duration);
  @override Duration difference(DateTime other) =>
      _asDateTime().difference(other);

  DateTime _asDateTime() =>
      new DateTime.fromMillisecondsSinceEpoch($unsafe.getTime());
}