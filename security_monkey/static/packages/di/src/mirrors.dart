library mirrors;

import 'dart:mirrors';
export 'dart:mirrors';

String getSymbolName(Symbol symbol) => MirrorSystem.getName(symbol);
