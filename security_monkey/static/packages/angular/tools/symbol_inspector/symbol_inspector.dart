library angular.tools.symbol_inspector;

import 'dart:mirrors';

class QualifiedSymbol {
  Symbol symbol;
  Symbol qualified;
  Symbol libraryName;

  QualifiedSymbol(this.symbol, this.qualified, this.libraryName);

  toString() => "QS($qualified)";
}

class LibraryInfo {
  List<QualifiedSymbol> names;
  Map<Symbol, List<Symbol>> symbolsUsedForName;

  LibraryInfo(this.names, this.symbolsUsedForName);
}

Iterable<Symbol> _getUsedSymbols(DeclarationMirror decl, seenDecls, path, onlyType) {

  if (seenDecls.containsKey(decl.qualifiedName)) return [];
  seenDecls[decl.qualifiedName] = true;

  if (decl.isPrivate) return [];

  path = "$path -> $decl";

  var used = [];

  if (decl is TypedefMirror) {
    TypedefMirror tddecl = decl;
    used.addAll(_getUsedSymbols(tddecl.referent, seenDecls, path, onlyType));
  }
  if (decl is FunctionTypeMirror) {
    FunctionTypeMirror ftdecl = decl;

    ftdecl.parameters.forEach((ParameterMirror p) {
      used.addAll(_getUsedSymbols(p.type, seenDecls, path, onlyType));
    });
    used.addAll(_getUsedSymbols(ftdecl.returnType, seenDecls, path, onlyType));
  }
  else if (decl is TypeMirror) {
    var tdecl = decl as TypeMirror;
    used.add(tdecl.qualifiedName);
  }


  if (!onlyType) {
    if (decl is ClassMirror) {
      ClassMirror cdecl = decl;
      cdecl.declarations.forEach((s, d) {
        try {
          used.addAll(_getUsedSymbols(d, seenDecls, path, false));
        } catch (e, s) {
          print("Got error [$e] when visiting $d\n$s");
        }
      });

    }

    if (decl is MethodMirror) {
      MethodMirror mdecl = decl;
      if (mdecl.parameters != null)
        mdecl.parameters.forEach((p) {
          used.addAll(_getUsedSymbols(p.type, seenDecls, path, true));
        });
      used.addAll(_getUsedSymbols(mdecl.returnType, seenDecls, path, true));
    }

    if (decl is VariableMirror) {
      VariableMirror vdecl = decl;
      used.addAll(_getUsedSymbols(vdecl.type, seenDecls, path, true));
    }
  }

  // Strip out type variables.
  if (decl is TypeMirror) {
    TypeMirror tdecl = decl;
    var typeVariables = tdecl.typeVariables.map((tv) => tv.qualifiedName);
    used = used.where((x) => !typeVariables.contains(x));
  }

  return used;
}

getSymbolsFromLibrary(String libraryName) {
// Set this to true to see how symbols are exported from angular.
  var SHOULD_PRINT_SYMBOL_TREE = false;

// TODO(deboer): Add types once Dart VM 1.2 is deprecated.
  LibraryInfo extractSymbols(/* LibraryMirror */ lib, [String printPrefix = ""]) {
    List<QualifiedSymbol> names = [];
    Map<Symbol, List<Symbol>> used = {};

    if (SHOULD_PRINT_SYMBOL_TREE) print(printPrefix + unwrapSymbol(lib.qualifiedName));
    printPrefix += "  ";
    lib.declarations.forEach((symbol, decl) {
      if (decl.isPrivate) return;

      // Work-around for dartbug.com/18271
      if (decl is TypedefMirror && unwrapSymbol(symbol).startsWith('_')) return;

      if (SHOULD_PRINT_SYMBOL_TREE) print(printPrefix + unwrapSymbol(symbol));
      names.add(new QualifiedSymbol(symbol, decl.qualifiedName, lib.qualifiedName));
      used[decl.qualifiedName] = _getUsedSymbols(decl, {}, "", false);
    });

    lib.libraryDependencies.forEach((/* LibraryDependencyMirror */ libDep) {
      LibraryMirror target = libDep.targetLibrary;
      if (!libDep.isExport) return;

      var childInfo = extractSymbols(target, printPrefix);
      var childNames = childInfo.names;

      // If there was a "show" or "hide" on the exported library, filter the results.
      // This API needs love :-(
      var showSymbols = [], hideSymbols = [];
      libDep.combinators.forEach((/* CombinatorMirror */ c) {
        if (c.isShow) {
          showSymbols.addAll(c.identifiers);
        }
        if (c.isHide) {
          hideSymbols.addAll(c.identifiers);
        }
      });

      // I don't think you can show and hide from the same library
      assert(showSymbols.isEmpty || hideSymbols.isEmpty);
      if (!showSymbols.isEmpty) {
        childNames = childNames.where((symAndLib) {
          return showSymbols.contains(symAndLib.symbol);
        });
      }
      if (!hideSymbols.isEmpty) {
        childNames = childNames.where((symAndLib) {
          return !hideSymbols.contains(symAndLib.symbol);
        });
      }

      names.addAll(childNames);
      used.addAll(childInfo.symbolsUsedForName);
    });
    return new LibraryInfo(names, used);
  };

  var lib = currentMirrorSystem().findLibrary(new Symbol(libraryName));
  return extractSymbols(lib);
}

var _SYMBOL_NAME = new RegExp('"(.*)"');
unwrapSymbol(sym) => _SYMBOL_NAME.firstMatch(sym.toString()).group(1);

assertSymbolNamesAreOk(List<String> allowedNames, LibraryInfo libraryInfo) {
  var _nameMap = {};
  var _qualifiedNameMap = {};

  allowedNames.forEach((x) => _nameMap[x] = true);

  libraryInfo.names.forEach((x) => _qualifiedNameMap[x.qualified] = true);

  var usedButNotExported = {};
  var exported = [];


  libraryInfo.names.forEach((nameInfo) {
    String name = unwrapSymbol(nameInfo.qualified);
    String libName = unwrapSymbol(nameInfo.libraryName);

    var key = "$name";
    if (_nameMap.containsKey(key)) {
      _nameMap[key] = false;

      // Check that all the exposed types are also exported
      assert(libraryInfo.symbolsUsedForName.containsKey(nameInfo.qualified));
      libraryInfo.symbolsUsedForName[nameInfo.qualified].forEach((usedSymbol) {
        if ("$usedSymbol".contains('"dart.')) return;
        if ("$usedSymbol" == 'Symbol("dynamic")') return;
        if ("$usedSymbol" == 'Symbol("void")') return;

        if (!_qualifiedNameMap.containsKey(usedSymbol)) {
          usedButNotExported.putIfAbsent(usedSymbol, () => []);
          usedButNotExported[usedSymbol].add(nameInfo.qualified);
        }
      });
      return;
    }

    exported.add(key);
  });
  if (exported.isNotEmpty) {
    throw "These symbols are exported thru the angular library, but it shouldn't be:\n"
          "${exported.join('\n')}";
  }

  bool needHeader = true;
  usedButNotExported.forEach((used, locs) {
    print("  ${unwrapSymbol(used)} : unexported, used from:");
    locs.forEach((l) {
      print("      ${unwrapSymbol(l)}");
    });
    print("");
  });

  // If there are keys that no longer need to be in the ALLOWED_NAMES list, complain.
  var keys = [];
  _nameMap.forEach((k,v) {
    if (v) keys.add(k);
  });
  if (keys.isNotEmpty) {
    throw "These whitelisted symbols are not used:\n${keys.join('\n')}";
  }
}
