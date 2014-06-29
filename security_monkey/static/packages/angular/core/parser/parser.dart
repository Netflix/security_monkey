library angular.core.parser;

import 'package:angular/core/parser/syntax.dart'
   show CallArguments;
export 'package:angular/core/parser/syntax.dart'
   show Visitor, Expression, BoundExpression, CallArguments;
export 'package:angular/core/parser/dynamic_parser.dart'
   show DynamicParser, DynamicParserBackend, ClosureMap;

typedef LocalsWrapper(context, locals);
typedef Getter(self);
typedef Setter(self, value);
typedef BoundGetter([locals]);
typedef BoundSetter(value, [locals]);
typedef MethodClosure(obj, List posArgs, Map namedArgs);

/// Placeholder for DI. The parser you are looking for is [DynamicParser].
abstract class Parser<T> {
  T call(String input);
}

abstract class ParserBackend<T> {
  bool isAssignable(T expression);

  T newChain(List expressions) => null;
  T newFormatter(T expression, String name, List arguments) => null;

  T newAssign(T target, T value) => null;
  T newConditional(T condition, T yes, T no) => null;

  T newAccessScope(String name) => null;
  T newAccessMember(T object, String name) => null;
  T newAccessKeyed(T object, T key) => null;

  T newCallScope(String name, CallArguments arguments) => null;
  T newCallFunction(T function, CallArguments arguments) => null;
  T newCallMember(T object, String name, CallArguments arguments) => null;

  T newPrefix(String operation, T expression) => null;
  T newPrefixPlus(T expression) => expression;
  T newPrefixMinus(T expression) =>
      newBinaryMinus(newLiteralZero(), expression);
  T newPrefixNot(T expression) => newPrefix('!', expression);

  T newBinary(String operation, T left, T right) => null;
  T newBinaryPlus(T left, T right) => newBinary('+', left, right);
  T newBinaryMinus(T left, T right) => newBinary('-', left, right);
  T newBinaryMultiply(T left, T right) => newBinary('*', left, right);
  T newBinaryDivide(T left, T right) => newBinary('/', left, right);
  T newBinaryModulo(T left, T right) => newBinary('%', left, right);
  T newBinaryTruncatingDivide(T left, T right) => newBinary('~/', left, right);
  T newBinaryLogicalAnd(T left, T right) => newBinary('&&', left, right);
  T newBinaryLogicalOr(T left, T right) => newBinary('||', left, right);
  T newBinaryEqual(T left, T right) => newBinary('==', left, right);
  T newBinaryNotEqual(T left, T right) => newBinary('!=', left, right);
  T newBinaryLessThan(T left, T right) => newBinary('<', left, right);
  T newBinaryGreaterThan(T left, T right) => newBinary('>', left, right);
  T newBinaryLessThanEqual(T left, T right) => newBinary('<=', left, right);
  T newBinaryGreaterThanEqual(T left, T right) => newBinary('>=', left, right);

  T newLiteralPrimitive(value) => null;
  T newLiteralArray(List elements) => null;
  T newLiteralObject(List<String> keys, List values) => null;
  T newLiteralNull() => newLiteralPrimitive(null);
  T newLiteralZero() => newLiteralNumber(0);
  T newLiteralBoolean(bool value) => newLiteralPrimitive(value);
  T newLiteralNumber(num value) => newLiteralPrimitive(value);
  T newLiteralString(String value) => null;
}
