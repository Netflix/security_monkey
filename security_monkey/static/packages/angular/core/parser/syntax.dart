library angular.core.parser.syntax;

import 'package:angular/core/parser/parser.dart' show LocalsWrapper;
import 'package:angular/core/parser/unparser.dart' show Unparser;
import 'package:angular/core/parser/utils.dart' show EvalError;
import 'package:angular/core/module_internal.dart';

abstract class Visitor {
  visit(Expression expression) => expression.accept(this);

  visitExpression(Expression expression) => null;
  visitChain(Chain expression) => visitExpression(expression);
  visitFormatter(Formatter expression) => visitExpression(expression);

  visitAssign(Assign expression) => visitExpression(expression);
  visitConditional(Conditional expression) => visitExpression(expression);

  visitAccessScope(AccessScope expression) => visitExpression(expression);
  visitAccessMember(AccessMember expression) => visitExpression(expression);
  visitAccessKeyed(AccessKeyed expression) => visitExpression(expression);

  visitCallScope(CallScope expression) => visitExpression(expression);
  visitCallFunction(CallFunction expression) => visitExpression(expression);
  visitCallMember(CallMember expression) => visitExpression(expression);

  visitBinary(Binary expression) => visitExpression(expression);

  visitPrefix(Prefix expression) => visitExpression(expression);

  visitLiteral(Literal expression) => visitExpression(expression);
  visitLiteralPrimitive(LiteralPrimitive expression) =>
      visitLiteral(expression);
  visitLiteralString(LiteralString expression) => visitLiteral(expression);
  visitLiteralArray(LiteralArray expression) => visitLiteral(expression);
  visitLiteralObject(LiteralObject expression) => visitLiteral(expression);
}

abstract class Expression {
  bool get isAssignable => false;
  bool get isChain => false;

  eval(scope, [FormatterMap formatters = defaultFormatterMap]) =>
      throw new EvalError("Cannot evaluate $this");
  assign(scope, value) =>
      throw new EvalError("Cannot assign to $this");
  bind(context, [LocalsWrapper wrapper]) =>
      new BoundExpression(this, context, wrapper);

  accept(Visitor visitor);
  String toString() => Unparser.unparse(this);
}

class BoundExpression {
  final Expression expression;
  final _context;
  final LocalsWrapper _wrapper;
  BoundExpression(this.expression, this._context, this._wrapper);

  call([locals]) => expression.eval(_computeContext(locals));
  assign(value, [locals]) => expression.assign(_computeContext(locals), value);

  _computeContext(locals) {
    if (locals == null) return _context;
    if (_wrapper != null) return _wrapper(_context, locals);
    throw new StateError("Locals $locals provided, but missing wrapper.");
  }
}

class Chain extends Expression {
  final List<Expression> expressions;
  Chain(this.expressions);
  bool get isChain => true;
  accept(Visitor visitor) => visitor.visitChain(this);
}

class Formatter extends Expression {
  final Expression expression;
  final String name;
  final List<Expression> arguments;
  Formatter(this.expression, this.name, this.arguments);
  accept(Visitor visitor) => visitor.visitFormatter(this);
}

class Assign extends Expression {
  final Expression target;
  final Expression value;
  Assign(this.target, this.value);
  accept(Visitor visitor) => visitor.visitAssign(this);
}

class Conditional extends Expression {
  final Expression condition;
  final Expression yes;
  final Expression no;
  Conditional(this.condition, this.yes, this.no);
  accept(Visitor visitor) => visitor.visitConditional(this);
}

class AccessScope extends Expression {
  final String name;
  AccessScope(this.name);
  bool get isAssignable => true;
  accept(Visitor visitor) => visitor.visitAccessScope(this);
}

class AccessMember extends Expression {
  final Expression object;
  final String name;
  AccessMember(this.object, this.name);
  bool get isAssignable => true;
  accept(Visitor visitor) => visitor.visitAccessMember(this);
}

class AccessKeyed extends Expression {
  final Expression object;
  final Expression key;
  AccessKeyed(this.object, this.key);
  bool get isAssignable => true;
  accept(Visitor visitor) => visitor.visitAccessKeyed(this);
}

class CallArguments {
  final List<Expression> positionals;
  final Map<String, Expression> named;
  const CallArguments(this.positionals, this.named);

  int get arity => positionals.length + named.length;

  Expression operator[](int index) {
    int split = positionals.length;
    return index < split ? positionals[index] : named.values.elementAt(index - split);
  }
}

class CallScope extends Expression {
  final String name;
  final CallArguments arguments;
  CallScope(this.name, this.arguments);
  accept(Visitor visitor) => visitor.visitCallScope(this);
}

class CallFunction extends Expression {
  final Expression function;
  final CallArguments arguments;
  CallFunction(this.function, this.arguments);
  accept(Visitor visitor) => visitor.visitCallFunction(this);
}

class CallMember extends Expression {
  final Expression object;
  final String name;
  final CallArguments arguments;
  CallMember(this.object, this.name, this.arguments);
  accept(Visitor visitor) => visitor.visitCallMember(this);
}

class Binary extends Expression {
  final String operation;
  final Expression left;
  final Expression right;
  Binary(this.operation, this.left, this.right);
  accept(Visitor visitor) => visitor.visitBinary(this);
}

class Prefix extends Expression {
  final String operation;
  final Expression expression;
  Prefix(this.operation, this.expression);
  accept(Visitor visitor) => visitor.visitPrefix(this);
}

abstract class Literal extends Expression {
}

class LiteralPrimitive extends Literal {
  final value;
  LiteralPrimitive(this.value);
  accept(Visitor visitor) => visitor.visitLiteralPrimitive(this);
}

class LiteralString extends Literal {
  final String value;
  LiteralString(this.value);
  accept(Visitor visitor) => visitor.visitLiteralString(this);
}

class LiteralArray extends Literal {
  final List<Expression> elements;
  LiteralArray(this.elements);
  accept(Visitor visitor) => visitor.visitLiteralArray(this);
}

class LiteralObject extends Literal {
  final List<String> keys;
  final List<Expression> values;
  LiteralObject(this.keys, this.values);
  accept(Visitor visitor) => visitor.visitLiteralObject(this);
}

const defaultFormatterMap = const _DefaultFormatterMap();

class _DefaultFormatterMap implements FormatterMap {
  const _DefaultFormatterMap();

  call(name) => throw 'No Formatter: $name found!';
  Type operator[](annotation) => null;
  forEach(fn) { }
  annotationsFor(type) => null;
}
