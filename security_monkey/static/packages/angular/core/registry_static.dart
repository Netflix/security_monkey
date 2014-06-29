library angular.core_static;

import 'package:angular/core/annotation_src.dart' show Injectable;
import 'package:angular/core/registry.dart';

@Injectable()
class StaticMetadataExtractor extends MetadataExtractor {
  final Map<Type, Iterable> metadataMap;
  final List empty = const [];

  StaticMetadataExtractor(this.metadataMap);

  Iterable call(Type type) {
    Iterable i = metadataMap[type];
    return i == null ? empty : i;
  }
}
