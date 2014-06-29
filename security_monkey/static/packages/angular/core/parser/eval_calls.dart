library angular.core.parser.eval_calls;

import 'package:angular/core/parser/parser.dart';
import 'package:angular/core/parser/syntax.dart' as syntax;
import 'package:angular/core/parser/utils.dart';
import 'package:angular/core/module_internal.dart';


class CallScope extends syntax.CallScope {
  final MethodClosure methodClosure;
  CallScope(name, this.methodClosure, arguments)
      : super(name, arguments);

  eval(scope, [FormatterMap formatters]) {
    var positionals = arguments.positionals;
    var posArgs = new List(positionals.length);
    for(var i = 0; i < positionals.length; i++) {
      posArgs[i] = positionals[i].eval(scope, formatters);
    }
    var namedArgs = {};
    arguments.named.forEach((name, Expression exp) {
      namedArgs[name] = exp.eval(scope, formatters);
    });
    if (methodClosure == null) {
      _throwUndefinedFunction(name);
    }
    return methodClosure(scope, posArgs, namedArgs);
  }
}

class CallMember extends syntax.CallMember {
  final MethodClosure methodClosure;
  CallMember(object, this.methodClosure, name, arguments)
      : super(object, name, arguments)
  {
    if (methodClosure == null) {
      _throwUndefinedFunction(name);
    }
  }

  eval(scope, [FormatterMap formatters]) {
    var positionals = arguments.positionals;
    var posArgs = new List(positionals.length);
    for(var i = 0; i < positionals.length; i++) {
      posArgs[i] = positionals[i].eval(scope, formatters);
    }
    var namedArgs = {};
    arguments.named.forEach((name, Expression exp) {
      namedArgs[name] = exp.eval(scope, formatters);
    });
    return methodClosure(object.eval(scope, formatters), posArgs, namedArgs);
  }
}

class CallFunction extends syntax.CallFunction {
  final ClosureMap closureMap;
  CallFunction(function, this.closureMap, arguments) : super(function, arguments);
  eval(scope, [FormatterMap formatters]) {
    var function  = this.function.eval(scope, formatters);
    if (function is! Function) {
      throw new EvalError('${this.function} is not a function');
    } else {
      List positionals = evalList(scope, arguments.positionals, formatters);
      if (arguments.named.isNotEmpty) {
        var named = new Map<Symbol, dynamic>();
        arguments.named.forEach((String name, value) {
          named[closureMap.lookupSymbol(name)] = value.eval(scope, formatters);
        });
        return Function.apply(function, positionals, named);
      } else {
        return relaxFnApply(function, positionals);
      }
    }
  }
}


_throwUndefinedFunction(name) {
  throw "Undefined function $name";
}
