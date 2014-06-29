library angular.core.parser.eval;

import 'package:angular/core/parser/syntax.dart' as syntax;
import 'package:angular/core/parser/utils.dart';
import 'package:angular/core/module_internal.dart';

export 'package:angular/core/parser/eval_access.dart';
export 'package:angular/core/parser/eval_calls.dart';

class Chain extends syntax.Chain {
  Chain(List<syntax.Expression> expressions) : super(expressions);
  eval(scope, [FormatterMap formatters]) {
    var result;
    for (int i = 0; i < expressions.length; i++) {
      var last = expressions[i].eval(scope, formatters);
      if (last != null) result = last;
    }
    return result;
  }
}

class Formatter extends syntax.Formatter {
  final List<syntax.Expression> allArguments;
  Formatter(syntax.Expression expression, String name, List<syntax.Expression> arguments,
         this.allArguments)
      : super(expression, name, arguments);

  eval(scope, [FormatterMap formatters]) =>
      Function.apply(formatters(name), evalList(scope, allArguments, formatters));
}

class Assign extends syntax.Assign {
  Assign(syntax.Expression target, value) : super(target, value);
  eval(scope, [FormatterMap formatters]) =>
      target.assign(scope, value.eval(scope, formatters));
}

class Conditional extends syntax.Conditional {
  Conditional(syntax.Expression condition,
              syntax.Expression yes, syntax.Expression no)
      : super(condition, yes, no);
  eval(scope, [FormatterMap formatters]) => toBool(condition.eval(scope, formatters))
      ? yes.eval(scope, formatters)
      : no.eval(scope, formatters);
}

class PrefixNot extends syntax.Prefix {
  PrefixNot(syntax.Expression expression) : super('!', expression);
  eval(scope, [FormatterMap formatters]) => !toBool(expression.eval(scope, formatters));
}

class Binary extends syntax.Binary {
  Binary(String operation, syntax.Expression left, syntax.Expression right):
      super(operation, left, right);
  eval(scope, [FormatterMap formatters]) {
    var left = this.left.eval(scope, formatters);
    switch (operation) {
      case '&&': return toBool(left) && toBool(this.right.eval(scope, formatters));
      case '||': return toBool(left) || toBool(this.right.eval(scope, formatters));
    }
    var right = this.right.eval(scope, formatters);

    // Null check for the operations.
    if (left == null || right == null) {
      switch (operation) {
        case '+':
          if (left != null) return left;
          if (right != null) return right;
          return 0;
        case '-':
          if (left != null) return left;
          if (right != null) return 0 - right;
          return 0;
      }
      return null;
    }

    switch (operation) {
      case '+'  : return autoConvertAdd(left, right);
      case '-'  : return left - right;
      case '*'  : return left * right;
      case '/'  : return left / right;
      case '~/' : return left ~/ right;
      case '%'  : return left % right;
      case '==' : return left == right;
      case '!=' : return left != right;
      case '<'  : return left < right;
      case '>'  : return left > right;
      case '<=' : return left <= right;
      case '>=' : return left >= right;
      case '^'  : return left ^ right;
      case '&'  : return left & right;
    }
    throw new EvalError('Internal error [$operation] not handled');
  }
}

class LiteralPrimitive extends syntax.LiteralPrimitive {
  LiteralPrimitive(dynamic value) : super(value);
  eval(scope, [FormatterMap formatters]) => value;
}

class LiteralString extends syntax.LiteralString {
  LiteralString(String value) : super(value);
  eval(scope, [FormatterMap formatters]) => value;
}

class LiteralArray extends syntax.LiteralArray {
  LiteralArray(List<syntax.Expression> elements) : super(elements);
  eval(scope, [FormatterMap formatters]) =>
      elements.map((e) => e.eval(scope, formatters)).toList();
}

class LiteralObject extends syntax.LiteralObject {
  LiteralObject(List<String> keys, List<syntax.Expression>values) : super(keys, values);
  eval(scope, [FormatterMap formatters]) =>
      new Map.fromIterables(keys, values.map((e) => e.eval(scope, formatters)));
}
