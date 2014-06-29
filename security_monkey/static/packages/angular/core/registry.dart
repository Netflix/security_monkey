library angular.core.registry;

import 'package:di/di.dart' show Injector;

abstract class AnnotationMap<K> {
  final Map<K, Type> _map = {};

  AnnotationMap(Injector injector, MetadataExtractor extractMetadata) {
    injector.types.forEach((type) {
      extractMetadata(type)
          .where((annotation) => annotation is K)
          .forEach((annotation) {
            _map[annotation] = type;
          });
    });
  }

  Type operator[](K annotation) {
    var value = _map[annotation];
    if (value == null) throw 'No $annotation found!';
    return value;
  }

  void forEach(fn(K, Type)) {
    _map.forEach(fn);
  }

  List<K> annotationsFor(Type type) {
    final res = <K>[];
    forEach((ann, annType) {
      if (annType == type) res.add(ann);
    });
    return res;
  }
}

abstract class AnnotationsMap<K> {
  final Map<K, List<Type>> map = {};

  AnnotationsMap(Injector injector, MetadataExtractor extractMetadata) {
    injector.types.forEach((type) {
      extractMetadata(type)
          .where((annotation) => annotation is K)
          .forEach((annotation) {
            map.putIfAbsent(annotation, () => []).add(type);
          });
    });
  }

  List operator[](K annotation) {
    var value = map[annotation];
    if (value == null) throw 'No $annotation found!';
    return value;
  }

  void forEach(fn(K, Type)) {
    map.forEach((annotation, types) {
      types.forEach((type) {
        fn(annotation, type);
      });
    });
  }

  List<K> annotationsFor(Type type) {
    var res = <K>[];
    forEach((ann, annType) {
      if (annType == type) res.add(ann);
    });
    return res;
  }
}

abstract class MetadataExtractor {
  Iterable call(Type type);
}
