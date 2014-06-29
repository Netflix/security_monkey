library angular.tools.transformers.referenced_uris;

import 'dart:async';

import 'package:analyzer/src/generated/ast.dart';
import 'package:analyzer/src/generated/element.dart';
import 'package:angular/tools/transformer/options.dart';
import 'package:barback/barback.dart';
import 'package:code_transformers/resolver.dart';
import 'package:path/path.dart' as path;

/// Gathers the contents of all URIs which are referenced by the contents of
/// the application.
/// Returns a map from URI to contents.
Future<Map<String, String>> gatherReferencedUris(Transform transform,
    Resolver resolver, TransformOptions options,
    {bool skipNonCached: false, bool templatesOnly: false}) {
  return new _Processor(transform, resolver, options, skipNonCached,
      templatesOnly).process();
}

class _Processor {
  final Transform transform;
  final Resolver resolver;
  final TransformOptions options;
  final Map<RegExp, String> templateUriRewrites = <RegExp, String>{};
  final bool skipNonCached;
  final bool templatesOnly;

  ConstructorElement cacheAnnotation;
  ConstructorElement componentAnnotation;

  static const String cacheAnnotationName =
    'angular.template_cache_annotation.NgTemplateCache';
  static const String componentAnnotationName = 'angular.core.annotation_src.Component';

  _Processor(this.transform, this.resolver, this.options, this.skipNonCached,
      this.templatesOnly) {
    for (var key in options.templateUriRewrites.keys) {
      templateUriRewrites[new RegExp(key)] = options.templateUriRewrites[key];
    }
  }

  /// Gathers the contents of all URIs which are to be cached.
  /// Returns a map from URI to contents.
  Future<Map<String, String>> process() {
    var cacheAnnotationType = resolver.getType(cacheAnnotationName);
    if (cacheAnnotationType != null &&
        cacheAnnotationType.unnamedConstructor != null) {
      cacheAnnotation = cacheAnnotationType.unnamedConstructor;
    }

    var componentAnnotationType = resolver.getType(componentAnnotationName);
    if (componentAnnotationType != null &&
        componentAnnotationType.unnamedConstructor != null) {
      componentAnnotation = componentAnnotationType.unnamedConstructor;
    } else {
      logger.warning('Unable to resolve $componentAnnotationName.');
    }

    var annotations = resolver.libraries
        .expand((lib) => lib.units)
        .expand((unit) => unit.types)
        .where((type) => type.node != null)
        .expand(_AnnotatedElement.fromElement)
        .where((e) =>
            (e.annotation.element == cacheAnnotation ||
            e.annotation.element == componentAnnotation))
        .toList();

    var uriToEntry = <String, _CacheEntry>{};
    annotations.where((anno) => anno.annotation.element == componentAnnotation)
        .expand(processComponentAnnotation)
        .forEach((entry) {
          uriToEntry[entry.uri] = entry;
        });
    if (!templatesOnly) {
      annotations.where((anno) => anno.annotation.element == cacheAnnotation)
          .expand(processCacheAnnotation)
          .forEach((entry) {
            uriToEntry[entry.uri] = entry;
          });
    }

    var futures = uriToEntry.values.map(cacheEntry);

    return Future.wait(futures).then((_) {
      var uriToContents = <String, String>{};
      for (var entry in uriToEntry.values) {
        if (entry.contents == null) continue;

        uriToContents[entry.uri] = entry.contents;
      }
      return uriToContents;
    });
  }

  /// Extracts the cacheable URIs from the Component annotation.
  List<_CacheEntry> processComponentAnnotation(_AnnotatedElement annotation) {
    var entries = <_CacheEntry>[];
    if (skipNonCached && isCachingSuppressed(annotation.element)) {
      return entries;
    }
    for (var arg in annotation.annotation.arguments.arguments) {
      if (arg is NamedExpression) {
        var paramName = arg.name.label.name;
        if (paramName == 'templateUrl') {
          var entry = extractString('templateUrl', arg.expression,
              annotation.element);
          if (entry != null) {
            entries.add(entry);
          }
        } else if (paramName == 'cssUrl' && !templatesOnly) {
          entries.addAll(extractListOrString(paramName, arg.expression,
              annotation.element));
        }
      }
    }

    return entries;
  }

  bool isCachingSuppressed(Element e) {
    if (cacheAnnotation == null) return false;
    AnnotatedNode node = e.node;
    for (var annotation in node.metadata) {
      if (annotation.element == cacheAnnotation) {
        for (var arg in annotation.arguments.arguments) {
          if (arg is NamedExpression && arg.name.label.name == 'cache') {
            var value = arg.expression;
            if (value is! BooleanLiteral) {
              warn('Expected boolean literal for NgTemplateCache.cache', e);
              return false;
            }
            return !value.value;
          }
        }
      }
    }
    return false;
  }

  List<_CacheEntry> processCacheAnnotation(_AnnotatedElement annotation) {
    var entries = <_CacheEntry>[];
    for (var arg in annotation.annotation.arguments.arguments) {
      if (arg is NamedExpression) {
        var paramName = arg.name.label.name;
        if (paramName == 'preCacheUrls') {
          entries.addAll(extractListOrString(paramName, arg.expression,
              annotation.element));
        }
      }
    }
    return entries;
  }

  List<_CacheEntry> extractListOrString(String paramName,
      Expression expression, Element element) {
    var entries = [];
    if (expression is StringLiteral) {
      var entry = uriToEntry(expression.stringValue, element);
      if (entry != null) {
        entries.add(entry);
      }
    } else if (expression is ListLiteral) {
      for (var value in expression.elements) {
        if (value is! StringLiteral) {
          warn('Expected a string literal in $paramName', element);
          continue;
        }
        var entry = uriToEntry(value.stringValue, element);
        if (entry != null) {
          entries.add(entry);
        }
      }
    } else {
      warn('$paramName must be a string or list literal.', element);
    }
    return entries;
  }

  _CacheEntry extractString(String paramName, Expression expression,
      Element element) {
    if (expression is StringLiteral) {
      return uriToEntry(expression.stringValue, element);
    }
    warn('$paramName must be a string literal.', element);
    return null;
  }

  Future<_CacheEntry> cacheEntry(_CacheEntry entry) {
    return transform.readInputAsString(entry.assetId).then((contents) {
      entry.contents = contents;
      return entry;
    }, onError: (e) {
      warn('Unable to find ${entry.uri} at ${entry.assetId}', entry.element);
    });
  }

  _CacheEntry uriToEntry(String uri, Element reference) {
    uri = rewriteUri(uri);
    if (Uri.parse(uri).scheme != '') {
      warn('Cannot cache non-local URIs. $uri', reference);
      return null;
    }
    if (path.url.isAbsolute(uri)) {
      var parts = path.posix.split(uri);
      if (parts[1] == 'packages') {
        var pkgPath = path.url.join('lib', path.url.joinAll(parts.skip(3)));
        return new _CacheEntry(uri, reference, new AssetId(parts[2], pkgPath));
      }
      warn('Cannot cache non-package absolute URIs. $uri', reference);
      return null;
    }
    var assetId = new AssetId(transform.primaryInput.id.package, uri);
    return new _CacheEntry(uri, reference, assetId);
  }

  String rewriteUri(String uri) {
    templateUriRewrites.forEach((regexp, replacement) {
      uri = uri.replaceFirst(regexp, replacement);
    });
    // Normalize packages/ uri's to be /packages/
    if (uri.startsWith('packages/')) {
      uri = '/' + uri;
    }
    return uri;
  }

  void warn(String msg, Element element) {
    logger.warning(msg, asset: resolver.getSourceAssetId(element),
        span: resolver.getSourceSpan(element));
  }

  TransformLogger get logger => transform.logger;
}

/// Wrapper for data related to a single cache entry.
class _CacheEntry {
  final String uri;
  final Element element;
  final AssetId assetId;
  String contents;

  _CacheEntry(this.uri, this.element, this.assetId);
}

/// Wrapper for annotation AST nodes to track the element they were declared on.
class _AnnotatedElement {
  /// The annotation node.
  final Annotation annotation;
  /// The element which the annotation was declared on.
  final Element element;

  _AnnotatedElement(this.annotation, this.element);

  static Iterable<_AnnotatedElement> fromElement(Element element) {
    AnnotatedNode node = element.node;
    return node.metadata.map(
        (annotation) => new _AnnotatedElement(annotation, element));
  }
}
