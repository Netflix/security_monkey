library angular.core.parser_dynamic;

@MirrorsUsed(targets: const [ DynamicClosureMap ], metaTargets: const [] )
import 'dart:mirrors';
import 'package:angular/core/parser/parser.dart';

class DynamicClosureMap implements ClosureMap {
  final Map<String, Symbol> symbols = {};
  Getter lookupGetter(String name) {
    var symbol = new Symbol(name);
    return (o) {
      if (o is Map) {
        return o[name];
      } else {
        return reflect(o).getField(symbol).reflectee;
      }
    };
  }

  Setter lookupSetter(String name) {
    var symbol = new Symbol(name);
    return (o, value) {
      if (o is Map) {
        return o[name] = value;
      } else {
        reflect(o).setField(symbol, value);
        return value;
      }
    };
  }

  MethodClosure lookupFunction(String name, CallArguments arguments) {
    var symbol = new Symbol(name);
    return (o, posArgs, namedArgs) {
      var sNamedArgs = {};
      namedArgs.forEach((name, value) {
        var symbol = symbols.putIfAbsent(name, () => new Symbol(name));
        sNamedArgs[symbol] = value;
      });
      if (o is Map) {
        var fn = o[name];
        if (fn is Function) {
          return Function.apply(fn, posArgs, sNamedArgs);
        } else {
          throw "Property '$name' is not of type function.";
        }
      } else {
        try {
          return reflect(o).invoke(symbol, posArgs, sNamedArgs).reflectee;
        } on NoSuchMethodError catch (e) {
          throw 'Undefined function $name';
        }
      }
    };
  }

  Symbol lookupSymbol(String name) => new Symbol(name);
}
