library angular.core.parser.dynamic_parser;

import 'package:angular/core/annotation_src.dart' hide Formatter;
import 'package:angular/core/module_internal.dart' show FormatterMap;

import 'package:angular/core/parser/parser.dart';
import 'package:angular/core/parser/lexer.dart';
import 'package:angular/core/parser/dynamic_parser_impl.dart';
import 'package:angular/core/parser/syntax.dart' show defaultFormatterMap;

import 'package:angular/core/parser/eval.dart';
import 'package:angular/core/parser/utils.dart' show EvalError;
import 'package:angular/utils.dart';

abstract class ClosureMap {
  Getter lookupGetter(String name);
  Setter lookupSetter(String name);
  Symbol lookupSymbol(String name);
  MethodClosure lookupFunction(String name, CallArguments arguments);
}

@Injectable()
class DynamicParser implements Parser<Expression> {
  final Lexer _lexer;
  final ParserBackend _backend;
  final Map<String, Expression> _cache = {};
  DynamicParser(this._lexer, this._backend);

  Expression call(String input) {
    if (input == null) input = '';
    return _cache.putIfAbsent(input, () => _parse(input));
  }

  Expression _parse(String input) {
    DynamicParserImpl parser = new DynamicParserImpl(_lexer, _backend, input);
    Expression expression = parser.parseChain();
    return new DynamicExpression(expression);
  }
}

class DynamicExpression extends Expression {
  final Expression _expression;
  DynamicExpression(this._expression);

  bool get isAssignable => _expression.isAssignable;
  bool get isChain => _expression.isChain;

  accept(Visitor visitor) => _expression.accept(visitor);
  toString() => _expression.toString();

  eval(scope, [FormatterMap formatters = defaultFormatterMap]) {
    try {
      return _expression.eval(scope, formatters);
    } on EvalError catch (e, s) {
      throw e.unwrap("$this", s);
    }
  }

  assign(scope, value) {
    try {
      return _expression.assign(scope, value);
    } on EvalError catch (e, s) {
      throw e.unwrap("$this", s);
    }
  }
}

@Injectable()
class DynamicParserBackend extends ParserBackend {
  final ClosureMap _closures;
  DynamicParserBackend(this._closures);

  bool isAssignable(Expression expression) => expression.isAssignable;

  Expression newFormatter(expression, name, arguments) {
    List allArguments = new List(arguments.length + 1);
    allArguments[0] = expression;
    allArguments.setAll(1, arguments);
    return new Formatter(expression, name, arguments, allArguments);
  }

  Expression newChain(expressions) => new Chain(expressions);
  Expression newAssign(target, value) => new Assign(target, value);
  Expression newConditional(condition, yes, no) =>
      new Conditional(condition, yes, no);

  Expression newAccessKeyed(object, key) => new AccessKeyed(object, key);
  Expression newCallFunction(function, arguments) =>
      new CallFunction(function, _closures, arguments);

  Expression newPrefixNot(expression) => new PrefixNot(expression);

  Expression newBinary(operation, left, right) =>
      new Binary(operation, left, right);

  Expression newLiteralPrimitive(value) => new LiteralPrimitive(value);
  Expression newLiteralArray(elements) => new LiteralArray(elements);
  Expression newLiteralObject(keys, values) => new LiteralObject(keys, values);
  Expression newLiteralString(value) => new LiteralString(value);

  Expression newAccessScope(name) {
    Getter getter;
    Setter setter;
    if (name == 'this') {
      getter = (o) => o;
    } else {
      _assertNotReserved(name);
      getter = _closures.lookupGetter(name);
      setter = _closures.lookupSetter(name);
    }
    return new AccessScopeFast(name, getter, setter);
  }

  Expression newAccessMember(object, name) {
    _assertNotReserved(name);
    Getter getter = _closures.lookupGetter(name);
    Setter setter = _closures.lookupSetter(name);
    return new AccessMemberFast(object, name, getter, setter);
  }

  Expression newCallScope(name, arguments) {
    _assertNotReserved(name);
    MethodClosure function = _closures.lookupFunction(name, arguments);
    return new CallScope(name, function, arguments);
  }

  Expression newCallMember(object, name, arguments) {
    _assertNotReserved(name);
    MethodClosure function = _closures.lookupFunction(name, arguments);
    return new CallMember(object, function, name, arguments);
  }

  _assertNotReserved(name) {
    if (isReservedWord(name)) {
      throw "Identifier '$name' is a reserved word.";
    }
  }
}

