library angular.tools.transformer.metadata_generator;

import 'package:analyzer/src/generated/element.dart';
import 'package:angular/tools/transformer/options.dart';
import 'package:barback/barback.dart';
import 'package:code_transformers/resolver.dart';
import 'package:path/path.dart' as path;

import 'metadata_extractor.dart';

class MetadataGenerator extends Transformer with ResolverTransformer {
  final TransformOptions options;

  MetadataGenerator(this.options, Resolvers resolvers) {
    this.resolvers = resolvers;
  }

  void applyResolver(Transform transform, Resolver resolver) {
    var asset = transform.primaryInput;
    var id = asset.id;
    var outputFilename = '${path.url.basenameWithoutExtension(id.path)}'
        '_static_metadata.dart';
    var outputPath = path.url.join(path.url.dirname(id.path), outputFilename);
    var outputId = new AssetId(id.package, outputPath);

    var extractor = new AnnotationExtractor(transform.logger, resolver,
        outputId);

    var outputBuffer = new StringBuffer();
    _writeHeader(asset.id, outputBuffer);

    var annotatedTypes = resolver.libraries
        .where((lib) => !lib.isInSdk)
        .expand((lib) => lib.units)
        .expand((unit) => unit.types)
        .map(extractor.extractAnnotations)
        .where((annotations) => annotations != null).toList();

    var libs = annotatedTypes.expand((type) => type.referencedLibraries)
        .toSet();

    var importPrefixes = <LibraryElement, String>{};
    var index = 0;
    for (var lib in libs) {
      if (lib.isDartCore) {
        importPrefixes[lib] = '';
        continue;
      }

      var prefix = 'import_${index++}';
      var url = resolver.getImportUri(lib, from: outputId);
      outputBuffer.write('import \'$url\' as $prefix;\n');
      importPrefixes[lib] = '$prefix.';
    }

    _writePreamble(outputBuffer);

    _writeClassPreamble(outputBuffer);
    for (var type in annotatedTypes) {
      type.writeClassAnnotations(
          outputBuffer, transform.logger, resolver, importPrefixes);
    }
    _writeClassEpilogue(outputBuffer);

    transform.addOutput(
          new Asset.fromString(outputId, outputBuffer.toString()));
    transform.addOutput(asset);
  }
}

void _writeHeader(AssetId id, StringSink sink) {
  var libPath = path.withoutExtension(id.path).replaceAll('/', '.').replaceAll('-', '_');
  sink.write('''
library ${id.package}.$libPath.generated_metadata;

import 'package:angular/core/registry.dart' show MetadataExtractor;
import 'package:di/di.dart' show Module;

''');
}

void _writePreamble(StringSink sink) {
  sink.write('''
Module get metadataModule => new Module()
    ..bind(MetadataExtractor, toValue: new _StaticMetadataExtractor());

class _StaticMetadataExtractor implements MetadataExtractor {
  Iterable call(Type type) {
    var annotations = typeAnnotations[type];
    if (annotations != null) {
      return annotations;
    }
    return [];
  }
}

''');
}

void _writeClassPreamble(StringSink sink) {
  sink.write('''
final Map<Type, Object> typeAnnotations = {
''');
}

void _writeClassEpilogue(StringSink sink) {
  sink.write('''
};
''');
}

void _writeFooter(StringSink sink) {
  sink.write('''
};
''');
}
