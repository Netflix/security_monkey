library angular.core.parser.dynamic_parser_impl;

import 'package:angular/core/parser/parser.dart' show ParserBackend;
import 'package:angular/core/parser/lexer.dart';
import 'package:angular/core/parser/syntax.dart';
import 'package:angular/core/parser/characters.dart';
import 'package:angular/utils.dart' show isReservedWord;

class DynamicParserImpl {
  final ParserBackend backend;
  final String input;
  final List<Token> tokens;
  int index = 0;

  DynamicParserImpl(Lexer lexer, this.backend, String input)
      : this.input = input, tokens = lexer.call(input);

  Token get next => peek(0);
  Token peek(int offset) => (index + offset < tokens.length)
      ? tokens[index + offset]
      : Token.EOF;

  parseChain() {
    bool isChain = false;
    while (optionalCharacter($SEMICOLON)) {
      isChain = true;
    }
    List expressions = [];
    while (index < tokens.length) {
      if (next.isCharacter($RPAREN) ||
          next.isCharacter($RBRACE) ||
          next.isCharacter($RBRACKET)) {
        error('Unconsumed token $next');
      }
      var expr = parseFormatter();
      expressions.add(expr);
      while (optionalCharacter($SEMICOLON)) {
        isChain = true;
      }
      if (isChain && expr is Formatter) {
        error('Cannot have a formatter in a chain');
      }
      if (!isChain && index < tokens.length) {
        error("'${next}' is an unexpected token", index);
      }
    }
    return (expressions.length == 1)
        ? expressions.first
        : backend.newChain(expressions);
  }

  parseFormatter() {
    var result = parseExpression();
    while (optionalOperator('|')) {
      String name = expectIdentifierOrKeyword();
      List arguments = [];
      while (optionalCharacter($COLON)) {
        // TODO(kasperl): Is this really supposed to be expressions?
        arguments.add(parseExpression());
      }
      result = backend.newFormatter(result, name, arguments);
    }
    return result;
  }

  parseExpression() {
    int start = next.index;
    var result = parseConditional();
    while (next.isOperator('=')) {
      if (!backend.isAssignable(result)) {
        int end = (index < tokens.length) ? next.index : input.length;
        String expression = input.substring(start, end);
        error('Expression $expression is not assignable');
      }
      expectOperator('=');
      result = backend.newAssign(result, parseConditional());
    }
    return result;
  }

  parseConditional() {
    int start = next.index;
    var result = parseLogicalOr();
    if (optionalOperator('?')) {
      var yes = parseExpression();
      if (!optionalCharacter($COLON)) {
        int end = (index < tokens.length) ? next.index : input.length;
        String expression = input.substring(start, end);
        error('Conditional expression $expression requires all 3 expressions');
      }
      var no = parseExpression();
      result = backend.newConditional(result, yes, no);
    }
    return result;
  }

  parseLogicalOr() {
    // '||'
    var result = parseLogicalAnd();
    while (optionalOperator('||')) {
      result = backend.newBinaryLogicalOr(result, parseLogicalAnd());
    }
    return result;
  }

  parseLogicalAnd() {
    // '&&'
    var result = parseEquality();
    while (optionalOperator('&&')) {
      result = backend.newBinaryLogicalAnd(result, parseEquality());
    }
    return result;
  }

  parseEquality() {
    // '==','!='
    var result = parseRelational();
    while (true) {
      if (optionalOperator('==')) {
        result = backend.newBinaryEqual(result, parseRelational());
      } else if (optionalOperator('!=')) {
        result = backend.newBinaryNotEqual(result, parseRelational());
      } else {
        return result;
      }
    }
  }

  parseRelational() {
    // '<', '>', '<=', '>='
    var result = parseAdditive();
    while (true) {
      if (optionalOperator('<')) {
        result = backend.newBinaryLessThan(result, parseAdditive());
      } else if (optionalOperator('>')) {
        result = backend.newBinaryGreaterThan(result, parseAdditive());
      } else if (optionalOperator('<=')) {
        result = backend.newBinaryLessThanEqual(result, parseAdditive());
      } else if (optionalOperator('>=')) {
        result = backend.newBinaryGreaterThanEqual(result, parseAdditive());
      } else {
        return result;
      }
    }
  }

  parseAdditive() {
    // '+', '-'
    var result = parseMultiplicative();
    while (true) {
      if (optionalOperator('+')) {
        result = backend.newBinaryPlus(result, parseMultiplicative());
      } else if (optionalOperator('-')) {
        result = backend.newBinaryMinus(result, parseMultiplicative());
      } else {
        return result;
      }
    }
  }

  parseMultiplicative() {
    // '*', '%', '/', '~/'
    var result = parsePrefix();
    while (true) {
      if (optionalOperator('*')) {
        result = backend.newBinaryMultiply(result, parsePrefix());
      } else if (optionalOperator('%')) {
        result = backend.newBinaryModulo(result, parsePrefix());
      } else if (optionalOperator('/')) {
        result = backend.newBinaryDivide(result, parsePrefix());
      } else if (optionalOperator('~/')) {
        result = backend.newBinaryTruncatingDivide(result, parsePrefix());
      } else {
        return result;
      }
    }
  }

  parsePrefix() {
    if (optionalOperator('+')) {
      // TODO(kasperl): This is different than the original parser.
      return backend.newPrefixPlus(parsePrefix());
    } else if (optionalOperator('-')) {
      return backend.newPrefixMinus(parsePrefix());
    } else if (optionalOperator('!')) {
      return backend.newPrefixNot(parsePrefix());
    } else {
      return parseAccessOrCallMember();
    }
  }

  parseAccessOrCallMember() {
    var result = parsePrimary();
    while (true) {
      if (optionalCharacter($PERIOD)) {
        String name = expectIdentifierOrKeyword();
        if (optionalCharacter($LPAREN)) {
          CallArguments arguments = parseCallArguments();
          expectCharacter($RPAREN);
          result = backend.newCallMember(result, name, arguments);
        } else {
          result = backend.newAccessMember(result, name);
        }
      } else if (optionalCharacter($LBRACKET)) {
        var key = parseExpression();
        expectCharacter($RBRACKET);
        result = backend.newAccessKeyed(result, key);
      } else if (optionalCharacter($LPAREN)) {
        CallArguments arguments = parseCallArguments();
        expectCharacter($RPAREN);
        result = backend.newCallFunction(result, arguments);
      } else {
        return result;
      }
    }
  }

  parsePrimary() {
    if (optionalCharacter($LPAREN)) {
      var result = parseFormatter();
      expectCharacter($RPAREN);
      return result;
    } else if (next.isKeywordNull || next.isKeywordUndefined) {
      advance();
      return backend.newLiteralNull();
    } else if (next.isKeywordTrue) {
      advance();
      return backend.newLiteralBoolean(true);
    } else if (next.isKeywordFalse) {
      advance();
      return backend.newLiteralBoolean(false);
    } else if (optionalCharacter($LBRACKET)) {
      List elements = parseExpressionList($RBRACKET);
      expectCharacter($RBRACKET);
      return backend.newLiteralArray(elements);
    } else if (next.isCharacter($LBRACE)) {
      return parseObject();
    } else if (next.isIdentifier) {
      return parseAccessOrCallScope();
    } else if (next.isNumber) {
      num value = next.toNumber();
      advance();
      return backend.newLiteralNumber(value);
    } else if (next.isString) {
      String value = next.toString();
      advance();
      return backend.newLiteralString(value);
    } else if (index >= tokens.length) {
      throw 'Unexpected end of expression: $input';
    } else {
      error('Unexpected token $next');
    }
  }

  parseAccessOrCallScope() {
    String name = expectIdentifierOrKeyword();
    if (!optionalCharacter($LPAREN)) return backend.newAccessScope(name);
    CallArguments arguments = parseCallArguments();
    expectCharacter($RPAREN);
    return backend.newCallScope(name, arguments);
  }

  parseObject() {
    List<String> keys = [];
    List values = [];
    expectCharacter($LBRACE);
    if (!optionalCharacter($RBRACE)) {
      do {
        String key = expectIdentifierOrKeywordOrString();
        keys.add(key);
        expectCharacter($COLON);
        values.add(parseExpression());
      } while (optionalCharacter($COMMA));
      expectCharacter($RBRACE);
    }
    return backend.newLiteralObject(keys, values);
  }

  List parseExpressionList(int terminator) {
    List result = [];
    if (!next.isCharacter(terminator)) {
      do {
        result.add(parseExpression());
       } while (optionalCharacter($COMMA));
    }
    return result;
  }

  CallArguments parseCallArguments() {
    if (next.isCharacter($RPAREN)) {
      return const CallArguments(const [], const {});
    }
    // Parse the positional arguments.
    List positionals = [];
    while (true) {
      if (peek(1).isCharacter($COLON)) break;
      positionals.add(parseExpression());
      if (!optionalCharacter($COMMA)) {
        return new CallArguments(positionals, const {});
      }
    }
    // Parse the named arguments.
    Map named = {};
    do {
      int marker = index;
      String name = expectIdentifierOrKeyword();
      if (isReservedWord(name)) {
        error("Cannot use Dart reserved word '$name' as named argument", marker);
      } else if (named.containsKey(name)) {
        error("Duplicate argument named '$name'", marker);
      }
      expectCharacter($COLON);
      named[name] = parseExpression();
    } while (optionalCharacter($COMMA));
    return new CallArguments(positionals, named);
  }

  bool optionalCharacter(int code) {
    if (next.isCharacter(code)) {
      advance();
      return true;
    } else {
      return false;
    }
  }

  bool optionalOperator(String operator) {
    if (next.isOperator(operator)) {
      advance();
      return true;
    } else {
      return false;
    }
  }

  void expectCharacter(int code) {
    if (optionalCharacter(code)) return;
    error('Missing expected ${new String.fromCharCode(code)}');
  }

  void expectOperator(String operator) {
    if (optionalOperator(operator)) return;
    error('Missing expected operator $operator');
  }

  String expectIdentifierOrKeyword() {
    if (!next.isIdentifier && !next.isKeyword) {
      error('Unexpected token $next, expected identifier or keyword');
    }
    String result = next.toString();
    advance();
    return result;
  }

  String expectIdentifierOrKeywordOrString() {
    if (!next.isIdentifier && !next.isKeyword && !next.isString) {
      error('Unexpected token $next, expected identifier, keyword, or string');
    }
    String result = next.toString();
    advance();
    return result;
  }

  void advance() {
    index++;
  }

  void error(message, [int index]) {
    if (index == null) index = this.index;
    String location = (index < tokens.length)
        ? 'at column ${tokens[index].index + 1} in'
        : 'the end of the expression';
    throw 'Parser Error: $message $location [$input]';
  }
}
