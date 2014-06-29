library angular.transformer;

import 'dart:async';
import 'dart:io';
import 'package:angular/tools/transformer/expression_generator.dart';
import 'package:angular/tools/transformer/metadata_generator.dart';
import 'package:angular/tools/transformer/static_angular_generator.dart';
import 'package:angular/tools/transformer/html_dart_references_generator.dart';
import 'package:angular/tools/transformer/options.dart';
import 'package:barback/barback.dart';
import 'package:code_transformers/resolver.dart';
import 'package:di/transformer/injector_generator.dart' show InjectorGenerator;
import 'package:di/transformer/options.dart' as di;
import 'package:path/path.dart' as path;


 /**
  * The Angular transformer, which internally runs several phases that will:
  *
  * * Extract all expressions for evaluation at runtime without using Mirrors.
  * * Extract all classes being dependency injected into a static injector.
  * * Extract all metadata for cached reflection.
  */
class AngularTransformerGroup implements TransformerGroup {
  final Iterable<Iterable> phases;

  AngularTransformerGroup(TransformOptions options)
      : phases = _createPhases(options);

  AngularTransformerGroup.asPlugin(BarbackSettings settings)
      : this(_parseSettings(settings.configuration));
}

TransformOptions _parseSettings(Map args) {
  // Default angular annotations for injectable types
  var annotations = [
      'angular.core.annotation_src.Injectable',
      'angular.core.annotation_src.Decorator',
      'angular.core.annotation_src.Controller',
      'angular.core.annotation_src.Component',
      'angular.core.annotation_src.Formatter'];
  annotations.addAll(_readStringListValue(args, 'injectable_annotations'));

  // List of types which are otherwise not indicated as being injectable.
  var injectedTypes = [
      'perf_api.Profiler',
  ];
  injectedTypes.addAll(_readStringListValue(args, 'injected_types'));

  var sdkDir = _readStringValue(args, 'dart_sdk', required: false);
  if (sdkDir == null) {
    // Assume the Pub executable is always coming from the SDK.
    sdkDir =  path.dirname(path.dirname(Platform.executable));
  }

  var diOptions = new di.TransformOptions(
      injectableAnnotations: annotations,
      injectedTypes: injectedTypes,
      sdkDirectory: sdkDir);

  return new TransformOptions(
      htmlFiles: _readStringListValue(args, 'html_files'),
      sdkDirectory: sdkDir,
      templateUriRewrites: _readStringMapValue(args, 'template_uri_rewrites'),
      diOptions: diOptions);
}

_readStringValue(Map args, String name, {bool required: true}) {
  var value = args[name];
  if (value == null) {
    if (required) {
      print('Angular transformer parameter "$name" '
          'has no value in pubspec.yaml.');
    }
    return null;
  }
  if (value is! String) {
    print('Angular transformer parameter "$name" value '
        'is not a string in pubspec.yaml.');
    return null;
  }
  return value;
}

_readStringListValue(Map args, String name) {
  var value = args[name];
  if (value == null) return [];
  var results = [];
  bool error;
  if (value is List) {
    results = value;
    error = value.any((e) => e is! String);
  } else if (value is String) {
    results = [value];
    error = false;
  } else {
    error = true;
  }
  if (error) {
    print('Angular transformer parameter "$name" '
        'has an invalid value in pubspec.yaml.');
  }
  return results;
}

Map<String, String> _readStringMapValue(Map args, String name) {
  var value = args[name];
  if (value == null) return {};
  if (value is! Map) {
    print('Angular transformer parameter "$name" '
        'is expected to be a map parameter.');
    return {};
  }
  if (value.keys.any((e) => e is! String) ||
      value.values.any((e) => e is! String)) {
    print('Angular transformer parameter "$name" '
        'is expected to be a map of strings.');
    return {};
  }
  return value;
}

List<List<Transformer>> _createPhases(TransformOptions options) {
  var resolvers = new Resolvers(options.sdkDirectory);
  return [
    [new HtmlDartReferencesGenerator(options)],
    [new _SerialTransformer([
      new ExpressionGenerator(options, resolvers),
      new InjectorGenerator(options.diOptions, resolvers),
      new MetadataGenerator(options, resolvers),
      new StaticAngularGenerator(options, resolvers)
    ])]
  ];
}

/// Helper which runs a group of transformers serially and ensures that
/// transformers with shared data are always applied in a specific order.
///
/// Transformers which communicate only via assets do not need this additional
/// synchronization.
///
/// This is used by Angular to ensure ordering of references to the cached
/// resolvers.
class _SerialTransformer extends Transformer {
  final Iterable<Transformer> _transformers;
  _SerialTransformer(this._transformers);

  Future<bool> isPrimary(input) =>
      Future.wait(_transformers.map((t) => t.isPrimary(input)))
          .then((l) => l.any((result) => result));

  Future apply(Transform transform) {
    return Future.forEach(_transformers, (t) {
      return new Future.value(t.isPrimary(transform.primaryInput))
        .then((isPrimary) {
          if (isPrimary) return t.apply(transform);
        });
    });
  }
}
