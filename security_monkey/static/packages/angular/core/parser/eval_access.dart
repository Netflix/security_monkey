library angular.core.parser.eval_access;

import 'package:angular/core/parser/parser.dart';
import 'package:angular/core/parser/syntax.dart' as syntax;
import 'package:angular/core/parser/utils.dart';
import 'package:angular/core/module_internal.dart';

class AccessScopeFast extends syntax.AccessScope with AccessFast {
  final Getter getter;
  final Setter setter;
  final bool isThis;
  AccessScopeFast(String name, this.getter, this.setter)
      : super(name),
        isThis = name == 'this';
  eval(scope, [FormatterMap formatters]) => isThis ? scope : _eval(scope);
  assign(scope, value) => _assign(scope, scope, value);
}

class AccessMemberFast extends syntax.AccessMember with AccessFast {
  final Getter getter;
  final Setter setter;
  AccessMemberFast(object, String name, this.getter, this.setter)
      : super(object, name);
  eval(scope, [FormatterMap formatters]) => _eval(object.eval(scope, formatters));
  assign(scope, value) => _assign(scope, object.eval(scope), value);
  _assignToNonExisting(scope, value) => object.assign(scope, { name: value });
}

class AccessKeyed extends syntax.AccessKeyed {
  AccessKeyed(object, key) : super(object, key);
  eval(scope, [FormatterMap formatters]) =>
      getKeyed(object.eval(scope, formatters), key.eval(scope, formatters));
  assign(scope, value) => setKeyed(object.eval(scope), key.eval(scope), value);
}

/**
 * The [AccessFast] mixin is used to share code between access expressions
 * where we have a pair of pre-compiled getter and setter functions that we
 * use to do the access the field.
 */
abstract class AccessFast {
  String get name;
  Getter get getter;
  Setter get setter;

  _eval(holder) {
    if (holder == null) return null;
    return (holder is Map) ? holder[name] : getter(holder);
  }

  _assign(scope, holder, value) {
    if (holder == null) {
      _assignToNonExisting(scope, value);
      return value;
    } else {
      return (holder is Map) ? (holder[name] = value) : setter(holder, value);
    }
  }

  // By default we don't do any assignments to non-existing holders. This
  // is overwritten for access to members.
  _assignToNonExisting(scope, value) => null;
}

