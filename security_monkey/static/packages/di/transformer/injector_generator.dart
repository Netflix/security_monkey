library di.transformer.injector_generator;

import 'dart:async';
import 'package:analyzer/src/generated/ast.dart';
import 'package:analyzer/src/generated/element.dart';
import 'package:barback/barback.dart';
import 'package:code_transformers/resolver.dart';
import 'package:di/transformer/options.dart';
import 'package:path/path.dart' as path;

import 'refactor.dart';

/**
 * Pub transformer which generates type factories for all injectable types
 * in the application.
 */
class InjectorGenerator extends Transformer with ResolverTransformer {
  final TransformOptions options;

  InjectorGenerator(this.options, Resolvers resolvers) {
    this.resolvers = resolvers;
  }

  Future<bool> shouldApplyResolver(Asset asset) => options.isDartEntry(asset);

  applyResolver(Transform transform, Resolver resolver) =>
      new _Processor(transform, resolver, options).process();
}

/** Class for processing a single apply.*/
class _Processor {

  /** Current transform. */
  final Transform transform;

  final Resolver resolver;
  final TransformOptions options;

  /** Asset ID for the location of the generated file, for imports. */
  AssetId _generatedAssetId;

  /** Resolved injectable annotations of the form `@Injectable()`. */
  final List<TopLevelVariableElement> injectableMetaConsts =
      <TopLevelVariableElement>[];

  /** Resolved injectable annotations of the form `@injectable`. */
  final List<ConstructorElement> injectableMetaConstructors =
      <ConstructorElement>[];

  /** Default list of injectable consts */
  static const List<String> defaultInjectableMetaConsts = const [
    'inject.inject'
  ];

  _Processor(this.transform, this.resolver, this.options);

  TransformLogger get logger => transform.logger;

  process() {
    _resolveInjectableMetadata();

    var id = transform.primaryInput.id;
    var outputFilename = '${path.url.basenameWithoutExtension(id.path)}'
        '_static_injector.dart';
    var outputPath = path.url.join(path.url.dirname(id.path), outputFilename);
    _generatedAssetId = new AssetId(id.package, outputPath);

    var constructors = _gatherConstructors();

    var injectLibContents = _generateInjectLibrary(constructors);
    transform.addOutput(
        new Asset.fromString(_generatedAssetId, injectLibContents));

    transformIdentifiers(transform, resolver,
        identifier: 'di.auto_injector.defaultInjector',
        replacement: 'createStaticInjector',
        importPrefix: 'generated_static_injector',
        importUrl: outputFilename);
  }

  /** Resolves the classes for the injectable annotations in the current AST. */
  void _resolveInjectableMetadata() {
    for (var constName in defaultInjectableMetaConsts) {
      var variable = resolver.getLibraryVariable(constName);
      if (variable != null) {
        injectableMetaConsts.add(variable);
      }
    }

    // Resolve the user-specified annotations
    // These may be either type names (constructors) or consts.
    for (var metaName in options.injectableAnnotations) {
      var variable = resolver.getLibraryVariable(metaName);
      if (variable != null) {
        injectableMetaConsts.add(variable);
        continue;
      }
      var cls = resolver.getType(metaName);
      if (cls != null && cls.unnamedConstructor != null) {
        injectableMetaConstructors.add(cls.unnamedConstructor);
        continue;
      }
      if (!DEFAULT_INJECTABLE_ANNOTATIONS.contains(metaName)) {
        logger.warning('Unable to resolve injectable annotation $metaName');
      }
    }
  }

  /** Finds all annotated constructors or annotated classes in the program. */
  Iterable<ConstructorElement> _gatherConstructors() {
    var constructors = resolver.libraries
        .expand((lib) => lib.units)
        .expand((compilationUnit) => compilationUnit.types)
        .map(_findInjectedConstructor)
        .where((ctor) => ctor != null).toList();

    constructors.addAll(_gatherInjectablesContents());
    constructors.addAll(_gatherManuallyInjected());

    return constructors.toSet();
  }

  /**
   * Get the constructors for all elements in the library @Injectables
   * statements. These are used to mark types as injectable which would
   * otherwise not be injected.
   *
   * Syntax is:
   *
   *     @Injectables(const[ElementName])
   *     library my.library;
   */
  Iterable<ConstructorElement> _gatherInjectablesContents() {
    var injectablesClass = resolver.getType('di.annotations.Injectables');
    if (injectablesClass == null) return const [];
    var injectablesCtor = injectablesClass.unnamedConstructor;

    var ctors = [];

    for (var lib in resolver.libraries) {
      var annotationIdx = 0;
      for (var annotation in lib.metadata) {
        if (annotation.element == injectablesCtor) {
          var libDirective = lib.definingCompilationUnit.node.directives
              .where((d) => d is LibraryDirective).single;
          var annotationDirective = libDirective.metadata[annotationIdx];
          var listLiteral = annotationDirective.arguments.arguments.first;

          for (var expr in listLiteral.elements) {
            var element = (expr as SimpleIdentifier).bestElement;
            if (element == null || element is! ClassElement) {
              _warn('Unable to resolve class $expr', element);
              continue;
            }
            var ctor = _findInjectedConstructor(element, true);
            if (ctor != null) {
              ctors.add(ctor);
            }
          }
        }
      }
    }
    return ctors;
  }

  /**
   * Finds all types which were manually specified as being injected in
   * the options file.
   */
  Iterable<ConstructorElement> _gatherManuallyInjected() {
    var ctors = [];
    for (var injectedName in options.injectedTypes) {
      var injectedClass = resolver.getType(injectedName);
      if (injectedClass == null) {
        logger.warning('Unable to resolve injected type name $injectedName');
        continue;
      }
      var ctor = _findInjectedConstructor(injectedClass, true);
      if (ctor != null) {
        ctors.add(ctor);
      }
    }
    return ctors;
  }

  /**
   * Checks if the element is annotated with one of the known injectablee
   * annotations.
   */
  bool _isElementAnnotated(Element e) {
    for (var meta in e.metadata) {
      if (meta.element is PropertyAccessorElement &&
          injectableMetaConsts.contains(meta.element.variable)) {
        return true;
      } else if (meta.element is ConstructorElement &&
          injectableMetaConstructors.contains(meta.element)) {
        return true;
      }
    }
    return false;
  }

  /**
   * Find an 'injected' constructor for the given class.
   * If [noAnnotation] is true then this will assume that the class is marked
   * for injection and will use the default constructor.
   */
  ConstructorElement _findInjectedConstructor(ClassElement cls,
      [bool noAnnotation = false]) {
    var classInjectedConstructors = [];
    if (_isElementAnnotated(cls) || noAnnotation) {
      var defaultConstructor = cls.unnamedConstructor;
      if (defaultConstructor == null) {
        _warn('${cls.name} cannot be injected because '
            'it does not have a default constructor.', cls);
      } else {
        classInjectedConstructors.add(defaultConstructor);
      }
    }

    classInjectedConstructors.addAll(
        cls.constructors.where(_isElementAnnotated));

    if (classInjectedConstructors.isEmpty) return null;
    if (classInjectedConstructors.length > 1) {
      _warn('${cls.name} has more than one constructor annotated for '
          'injection.', cls);
      return null;
    }

    var ctor = classInjectedConstructors.single;
    if (!_validateConstructor(ctor)) return null;

    return ctor;
  }

  /**
   * Validates that the constructor is injectable and emits warnings for any
   * errors.
   */
  bool _validateConstructor(ConstructorElement ctor) {
    var cls = ctor.enclosingElement;
    if (cls.isAbstract && !ctor.isFactory) {
      _warn('${cls.name} cannot be injected because '
          'it is an abstract type with no factory constructor.', cls);
      return false;
    }
    if (cls.isPrivate) {
      _warn('${cls.name} cannot be injected because it is a private type.',
          cls);
      return false;
    }
    if (resolver.getImportUri(cls.library, from: _generatedAssetId) == null) {
      _warn('${cls.name} cannot be injected because '
          'the containing file cannot be imported.', cls);
      return false;
    }
    if (!cls.typeParameters.isEmpty) {
      _warn('${cls.name} is a parameterized type.', cls);
      // Only warn.
    }
    if (ctor.name != '') {
      _warn('Named constructors cannot be injected.', ctor);
      return false;
    }
    for (var param in ctor.parameters) {
      var type = param.type;
      if (type is InterfaceType &&
          type.typeArguments.any((t) => !t.isDynamic)) {
        _warn('${cls.name} cannot be injected because '
            '${param.type} is a parameterized type.', ctor);
        return false;
      }
      if (type.isDynamic) {
        _warn('${cls.name} cannot be injected because parameter type '
          '${param.name} cannot be resolved.', ctor);
        return false;
      }
    }
    return true;
  }

  /**
   * Creates a library file for the specified constructors.
   */
  String _generateInjectLibrary(Iterable<ConstructorElement> constructors) {
    var prefixes = <LibraryElement, String>{};

    var ctorTypes = constructors.map((ctor) => ctor.enclosingElement).toSet();
    var paramTypes = constructors.expand((ctor) => ctor.parameters)
        .map((param) => param.type.element).toSet();

    var usedLibs = new Set<LibraryElement>();
    String resolveClassName(ClassElement type) {
      var library = type.library;
      usedLibs.add(library);

      var prefix = prefixes[library];
      if (prefix == null) {
        prefix = prefixes[library] =
            library.isDartCore ? '' : 'import_${prefixes.length}';
      }
      if (prefix.isNotEmpty) {
        prefix = '$prefix.';
      }
      return '$prefix${type.name}';
    }

    var factoriesBuffer = new StringBuffer();
    for (var ctor in constructors) {
      var type = ctor.enclosingElement;
      var typeName = resolveClassName(type);
      factoriesBuffer.write('  $typeName: (f) => new $typeName(');
      var params = ctor.parameters.map((param) {
        var typeName = resolveClassName(param.type.element);
        var annotations = [];
        if (param.metadata.isNotEmpty) {
          annotations = param.metadata.map(
              (item) => resolveClassName(item.element.returnType.element));
        }
        var annotationsSuffix =
            annotations.isNotEmpty ? ', ${annotations.first}' : '';
        return 'f($typeName$annotationsSuffix)';
      });
      factoriesBuffer.write('${params.join(', ')}),\n');
    }

    var outputBuffer = new StringBuffer();

    _writeStaticInjectorHeader(transform.primaryInput.id, outputBuffer);
    usedLibs.forEach((lib) {
      if (lib.isDartCore) return;
      var uri = resolver.getImportUri(lib, from: _generatedAssetId);
      outputBuffer.write('import \'$uri\' as ${prefixes[lib]};\n');
    });
    _writePreamble(outputBuffer);
    outputBuffer.write(factoriesBuffer);
    _writeFooter(outputBuffer);

    return outputBuffer.toString();
  }

  void _warn(String msg, Element element) {
     logger.warning(msg, asset: resolver.getSourceAssetId(element),
        span: resolver.getSourceSpan(element));
  }
}

void _writeStaticInjectorHeader(AssetId id, StringSink sink) {
  var libName = path.withoutExtension(id.path).replaceAll('/', '.');
  libName = libName.replaceAll('-', '_');
  sink.write('''
library ${id.package}.$libName.generated_static_injector;

import 'package:di/di.dart';
import 'package:di/static_injector.dart';

''');
}

void _writePreamble(StringSink sink) {
  sink.write('''
Injector createStaticInjector({List<Module> modules, String name,
    bool allowImplicitInjection: false}) =>
  new StaticInjector(modules: modules, name: name,
      allowImplicitInjection: allowImplicitInjection,
      typeFactories: factories);

final Map<Type, TypeFactory> factories = <Type, TypeFactory>{
''');
}

void _writeFooter(StringSink sink) {
  sink.write('''
};
''');
}
