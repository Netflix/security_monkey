library angular.core.parser_static;

import 'package:angular/core/parser/parser.dart';


class StaticClosureMap extends ClosureMap {
  final Map<String, Getter> getters;
  final Map<String, Setter> setters;
  final Map<String, Symbol> symbols;

  StaticClosureMap(this.getters, this.setters, this.symbols);

  Getter lookupGetter(String name) {
    Getter getter = getters[name];
    if (getter == null) throw "No getter for '$name'.";
    return getter;
  }

  Setter lookupSetter(String name) {
    Setter setter = setters[name];
    if (setter == null) throw "No setter for '$name'.";
    return setter;
  }

  MethodClosure lookupFunction(String name, CallArguments arguments) {
    var fn = lookupGetter(name);
    return (o, posArgs, namedArgs) {
      var sNamedArgs = {};
      namedArgs.forEach((name, value) => sNamedArgs[symbols[name]] = value);
      if (o is Map) {
        var fn = o[name];
        if (fn is Function) {
          return Function.apply(fn, posArgs, sNamedArgs);
        } else {
          throw "Property '$name' is not of type function.";
        }
      } else {
        return Function.apply(fn(o), posArgs, sNamedArgs);
      }
    };
  }

  Symbol lookupSymbol(String name) {
    Symbol symbol = symbols[name];
    if (symbol == null) throw "No symbol for '$name'.";
    return symbol;
  }
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
