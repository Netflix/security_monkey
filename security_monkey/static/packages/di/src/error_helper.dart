library di.error_helper;

import 'package:di/di.dart';
import 'package:di/src/base_injector.dart';

String error(ResolutionContext resolving, message, [Key appendDependency]) {
  if (appendDependency != null) {
    resolving = new ResolutionContext(resolving.depth + 1, appendDependency, resolving);
  }

  String graph = resolvedTypes(resolving).reversed.join(' -> ');

  return '$message (resolving $graph)';
}

List<Key> resolvedTypes(ResolutionContext resolving) {
  List resolved = [];
  while (resolving.depth != 0) {
    resolved.add(resolving.key);
    resolving = resolving.parent;
  }
  return resolved;
}
