part of angular.core.parser.lexer;

class Token {
  static const Token EOF = const Token._(-1);
  final int index;
  const Token._(this.index);

  bool get isIdentifier => false;
  bool get isString => false;
  bool get isNumber => false;

  bool isCharacter(int code) => false;
  bool isOperator(String operator) => false;

  bool get isKeyword => false;
  bool get isKeywordNull => false;
  bool get isKeywordUndefined => false;
  bool get isKeywordTrue => false;
  bool get isKeywordFalse => false;

  num toNumber() => null;
}

class CharacterToken extends Token {
  final int _code;
  CharacterToken(int index, this._code) : super._(index);
  bool isCharacter(int code) => _code == code;
  String toString() => new String.fromCharCode(_code);
}

class IdentifierToken extends Token {
  final String _text;
  final bool _isKeyword;
  IdentifierToken(int index, this._text, this._isKeyword) : super._(index);
  bool get isIdentifier => !_isKeyword;
  bool get isKeyword => _isKeyword;
  bool get isKeywordNull => _isKeyword && _text == "null";
  bool get isKeywordUndefined => _isKeyword && _text == "undefined";
  bool get isKeywordTrue => _isKeyword && _text == "true";
  bool get isKeywordFalse => _isKeyword && _text == "false";
  String toString() => _text;
}

class OperatorToken extends Token {
  final String _text;
  OperatorToken(int index, this._text) : super._(index);
  bool isOperator(String operator) => _text == operator;
  String toString() => _text;
}

class NumberToken extends Token {
  final num _value;
  NumberToken(int index, this._value) : super._(index);
  bool get isNumber => true;
  num toNumber() => _value;
  String toString() => "$_value";
}

class StringToken extends Token {
  final String input;
  final String _value;
  StringToken(int index, this.input, this._value) : super._(index);
  bool get isString => true;
  String toString() => _value;
}
