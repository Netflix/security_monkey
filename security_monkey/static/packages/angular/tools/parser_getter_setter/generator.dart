import 'package:angular/core/parser/parser.dart';
import 'package:angular/utils.dart' show isReservedWord;

class DartGetterSetterGen extends ParserBackend {
  final properties = new Set<String>();
  final calls = new Set<String>();
  final symbols = new Set<String>();

  bool isAssignable(expression) => true;

  registerAccess(String name) {
    if (isReservedWord(name)) return;
    properties.add(name);
  }

  registerCall(String name, CallArguments arguments) {
    if (isReservedWord(name)) return;
    calls.add(name);
    symbols.addAll(arguments.named.keys);
  }

  newAccessScope(String name) => registerAccess(name);
  newAccessMember(var object, String name) => registerAccess(name);
  newCallScope(String name, CallArguments arguments) =>
      registerCall(name, arguments);
  newCallMember(var object, String name, CallArguments arguments) =>
      registerCall(name, arguments);
}

class ParserGetterSetter {
  final Parser parser;
  final ParserBackend backend;
  ParserGetterSetter(this.parser, this.backend);

  generateParser(List<String> exprs, StringSink sink) {
    exprs.forEach((expr) {
      try {
        parser(expr);
      } catch (e) {
        // Ignore exceptions.
      }
    });

    DartGetterSetterGen backend = this.backend;
    sink.write(generateClosureMap(backend.properties, backend.calls,
                                  backend.symbols));
  }

  generateClosureMap(Set<String> properties,
                     Set<String> calls,
                     Set<String> symbols) {
    var getters = new Set.from(properties)..addAll(calls);
    return '''
StaticClosureMap closureMap = new StaticClosureMap(
  ${generateGetterMap(getters)},
  ${generateSetterMap(properties)},
  ${generateSymbolMap(symbols)});
''';
  }

  generateGetterMap(Iterable<String> keys) {
    var lines = keys.map((key) => '    r"${key}": (o) => o.$key');
    return '{\n${lines.join(",\n")}\n  }';
  }

  generateSetterMap(Iterable<String> keys) {
    var lines = keys.map((key) => '    r"${key}": (o,v) => o.$key = v');
    return '{\n${lines.join(",\n")}\n  }';
  }

  generateSymbolMap(Set<String> symbols) {
    var lines = symbols.map((key) => '    r"${key}": #$key');
    return '{\n${lines.join(",\n")}\n  }';
  }
}
