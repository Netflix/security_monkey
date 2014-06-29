part of angular.watch_group;


/**
 * RULES:
 *  - ASTs are reusable. Don't store scope/instance refs there
 *  - Parent knows about children, not the other way around.
 */
abstract class AST {
  static final String _CONTEXT = '#';
  final String expression;
  AST(expression)
      : expression = expression.startsWith('#.')
          ? expression.substring(2)
          : expression
  {
    assert(expression!=null);
  }
  WatchRecord<_Handler> setupWatch(WatchGroup watchGroup);
  String toString() => expression;
}

/**
 * SYNTAX: _context_
 *
 * This represent the initial _context_ for evaluation.
 */
class ContextReferenceAST extends AST {
  ContextReferenceAST(): super(AST._CONTEXT);
  WatchRecord<_Handler> setupWatch(WatchGroup watchGroup) =>
      new _ConstantWatchRecord(watchGroup, expression, watchGroup.context);
}

/**
 * SYNTAX: _context_
 *
 * This represent the initial _context_ for evaluation.
 */
class ConstantAST extends AST {
  final constant;

  ConstantAST(constant, [String expression])
      : constant = constant,
        super(expression == null
            ? constant is String ? '"$constant"' : '$constant'
            : expression);

  WatchRecord<_Handler> setupWatch(WatchGroup watchGroup) =>
      new _ConstantWatchRecord(watchGroup, expression, constant);
}

/**
 * SYNTAX: lhs.name.
 *
 * This is the '.' dot operator.
 */
class FieldReadAST extends AST {
  AST lhs;
  final String name;

  FieldReadAST(lhs, name)
      : lhs = lhs,
        name = name,
        super('$lhs.$name');

  WatchRecord<_Handler> setupWatch(WatchGroup watchGroup) =>
      watchGroup.addFieldWatch(lhs, name, expression);
}

/**
 * SYNTAX: fn(arg0, arg1, ...)
 *
 * Invoke a pure function. Pure means that the function has no state, and
 * therefore it needs to be re-computed only if its args change.
 */
class PureFunctionAST extends AST {
  final String name;
  final /* dartbug.com/16401 Function */ fn;
  final List<AST> argsAST;

  PureFunctionAST(name, this.fn, argsAST)
      : argsAST = argsAST,
        name = name,
        super('$name(${_argList(argsAST)})');

  WatchRecord<_Handler> setupWatch(WatchGroup watchGroup) =>
      watchGroup.addFunctionWatch(fn, argsAST, const {}, expression, true);
}

/**
 * SYNTAX: fn(arg0, arg1, ...)
 *
 * Invoke a pure function. Pure means that the function has no state, and
 * therefore it needs to be re-computed only if its args change.
 */
class ClosureAST extends AST {
  final String name;
  final /* dartbug.com/16401 Function */ fn;
  final List<AST> argsAST;

  ClosureAST(name, this.fn, argsAST)
      : argsAST = argsAST,
        name = name,
        super('$name(${_argList(argsAST)})');

  WatchRecord<_Handler> setupWatch(WatchGroup watchGroup) =>
      watchGroup.addFunctionWatch(fn, argsAST, const {}, expression, false);
}

/**
 * SYNTAX: lhs.method(arg0, arg1, ...)
 *
 * Invoke a method on [lhs] object.
 */
class MethodAST extends AST {
  final AST lhsAST;
  final String name;
  final List<AST> argsAST;
  final Map<Symbol, AST> namedArgsAST;

  MethodAST(lhsAST, name, argsAST, [this.namedArgsAST = const {}])
      : lhsAST = lhsAST,
        name = name,
        argsAST = argsAST,
        super('$lhsAST.$name(${_argList(argsAST)})');

  WatchRecord<_Handler> setupWatch(WatchGroup watchGroup) =>
      watchGroup.addMethodWatch(lhsAST, name, argsAST, namedArgsAST, expression);
}


class CollectionAST extends AST {
  final AST valueAST;
  CollectionAST(valueAST)
      : valueAST = valueAST,
        super('#collection($valueAST)');

  WatchRecord<_Handler> setupWatch(WatchGroup watchGroup) =>
      watchGroup.addCollectionWatch(valueAST);
}

String _argList(List<AST> items) => items.join(', ');

/**
 * The name is a bit oxymoron, but it is essentially the NullObject pattern.
 *
 * This allows children to set a handler on this Record and then let it write
 * the initial constant value to the forwarding Record.
 */
class _ConstantWatchRecord extends WatchRecord<_Handler> {
  final currentValue;
  final _Handler handler;

  _ConstantWatchRecord(WatchGroup watchGroup, String expression, currentValue)
      : currentValue = currentValue,
        handler = new _ConstantHandler(watchGroup, expression, currentValue);

  bool check() => false;
  void remove() => null;

  get field => null;
  get previousValue => null;
  get object => null;
  set object(_) => null;
  get nextChange => null;
}

