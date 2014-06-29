library di.transformer.options;

import 'dart:async';

import 'package:barback/barback.dart';
import 'package:code_transformers/resolver.dart';

const List<String> DEFAULT_INJECTABLE_ANNOTATIONS =
    const ['di.annotations.Injectable'];

/// Returns either a bool or a Future<bool> when complete.
typedef EntryFilter(Asset asset);

/** Options used by DI transformers */
class TransformOptions {

  /**
   * Filter to determine which assets should be modified.
   */
  final EntryFilter entryFilter;

  /**
   * List of additional annotations which are used to indicate types as being
   * injectable.
   */
  final List<String> injectableAnnotations;

  /**
   * Set of additional types which should be injected.
   */
  final Set<String> injectedTypes;

  /**
   * Path to the Dart SDK directory, for resolving Dart libraries.
   */
  final String sdkDirectory;

  TransformOptions({EntryFilter entryFilter, String sdkDirectory,
      List<String> injectableAnnotations, List<String> injectedTypes})
    : entryFilter = entryFilter != null ? entryFilter : isPossibleDartEntry,
      sdkDirectory = sdkDirectory,
      injectableAnnotations =
          (injectableAnnotations != null ? injectableAnnotations : [])
              ..addAll(DEFAULT_INJECTABLE_ANNOTATIONS),
      injectedTypes =
          new Set.from(injectedTypes != null ? injectedTypes : []) {
    if (sdkDirectory == null)
      throw new ArgumentError('sdkDirectory must be provided.');
  }

  Future<bool> isDartEntry(Asset asset) => new Future.value(entryFilter(asset));
}
