library angular.metadata_extractor;

import 'package:analyzer/src/generated/ast.dart';
import 'package:analyzer/src/generated/element.dart';
import 'package:analyzer/src/generated/parser.dart' show ResolutionCopier;
import 'package:analyzer/src/generated/scanner.dart';
import 'package:analyzer/src/generated/utilities_dart.dart' show ParameterKind;
import 'package:barback/barback.dart';
import 'package:code_transformers/resolver.dart';

class AnnotatedType {
  final ClassElement type;
  List<Annotation> annotations;

  AnnotatedType(this.type);

  /**
   * Finds all the libraries referenced by the annotations
   */
  Iterable<LibraryElement> get referencedLibraries {
    var libs = new Set();
    libs.add(type.library);

    var libCollector = new _LibraryCollector();
    for (var annotation in annotations) {
      annotation.accept(libCollector);
    }
    libs.addAll(libCollector.libraries);

    return libs;
  }

  void writeClassAnnotations(StringBuffer sink, TransformLogger logger,
      Resolver resolver, Map<LibraryElement, String> prefixes) {
    sink.write('  ${prefixes[type.library]}${type.name}: const [\n');
    var writer = new _AnnotationWriter(sink, prefixes);
    for (var annotation in annotations) {
      sink.write('    ');
      if (writer.writeAnnotation(annotation)) {
        sink.write(',\n');
      } else {
        sink.write('null,\n');
        logger.warning('Unable to serialize annotation $annotation.',
            asset: resolver.getSourceAssetId(annotation.parent.element),
            span: resolver.getSourceSpan(annotation.parent.element));
      }
    }
    sink.write('  ],\n');
  }
}

/**
 * Helper which finds all libraries referenced within the provided AST.
 */
class _LibraryCollector extends GeneralizingAstVisitor {
  final Set<LibraryElement> libraries = new Set<LibraryElement>();
  void visitSimpleIdentifier(SimpleIdentifier s) {
    var element = s.bestElement;
    if (element != null) {
      libraries.add(element.library);
    }
  }
}

/**
 * Helper class which writes annotations out to the buffer.
 * This does not support every syntax possible, but will return false when
 * the annotation cannot be serialized.
 */
class _AnnotationWriter {
  final StringBuffer sink;
  final Map<LibraryElement, String> prefixes;

  _AnnotationWriter(this.sink, this.prefixes);

  /**
   * Returns true if the annotation was successfully serialized.
   * If the annotation could not be written then the buffer is returned to its
   * original state.
   */
  bool writeAnnotation(Annotation annotation) {
    // Record the current location in the buffer and if writing fails then
    // back up the buffer to where we started.
    var len = sink.length;
    if (!_writeAnnotation(annotation)) {
      var str = sink.toString();
      sink.clear();
      sink.write(str.substring(0, len));
      return false;
    }
    return true;
  }

   bool _writeAnnotation(Annotation annotation) {
    var element = annotation.element;
    if (element is ConstructorElement) {
      sink.write('const ${prefixes[element.library]}'
          '${element.enclosingElement.name}');
      // Named constructors
      if (!element.name.isEmpty) {
        sink.write('.${element.name}');
      }
      sink.write('(');
      if (!_writeArguments(annotation)) return false;
      sink.write(')');
      return true;
    } else if (element is PropertyAccessorElement) {
      sink.write('${prefixes[element.library]}${element.name}');
      return true;
    }

    return false;
  }

  /** Writes the arguments for a type constructor. */
  bool _writeArguments(Annotation annotation) {
    var args = annotation.arguments;
    var index = 0;
    for (var arg in args.arguments) {
      if (arg is NamedExpression) {
        sink.write('${arg.name.label.name}: ');
        if (!_writeExpression(arg.expression)) return false;
      } else {
        if (!_writeExpression(arg)) return false;
      }
      if (++index < args.arguments.length) {
        sink.write(', ');
      }
    }
    return true;
  }

  /** Writes an expression. */
  bool _writeExpression(Expression expression) {
    if (expression is StringLiteral) {
      sink.write(expression.toSource());
      return true;
    }
    if (expression is ListLiteral) {
      sink.write('const [');
      for (var element in expression.elements) {
        if (!_writeExpression(element)) return false;
        sink.write(',');
      }
      sink.write(']');
      return true;
    }
    if (expression is MapLiteral) {
      sink.write('const {');
      var index = 0;
      for (var entry in expression.entries) {
        if (!_writeExpression(entry.key)) return false;
        sink.write(': ');
        if (!_writeExpression(entry.value)) return false;
        if (++index < expression.entries.length) {
          sink.write(', ');
        }
      }
      sink.write('}');
      return true;
    }
    if (expression is Identifier) {
      var element = expression.bestElement;
      if (element == null || !element.isPublic) return false;

      if (element is ClassElement) {
        sink.write('${prefixes[element.library]}${element.name}');
        return true;
      }
      if (element is PropertyAccessorElement) {
        var variable = element.variable;
        if (variable is FieldElement) {
          var cls = variable.enclosingElement;
          sink.write('${prefixes[cls.library]}${cls.name}.${variable.name}');
          return true;
        } else if (variable is TopLevelVariableElement) {
          sink.write('${prefixes[variable.library]}${variable.name}');
          return true;
        }
      }

      if (element is MethodElement) {
        var cls = element.enclosingElement;
        sink.write('${prefixes[cls.library]}${cls.name}.${element.name}');
        return true;
      }
    }
    if (expression is BooleanLiteral || expression is DoubleLiteral ||
        expression is IntegerLiteral || expression is NullLiteral) {
      sink.write(expression.toSource());
      return true;
    }
    return false;
  }
}

class AnnotationExtractor {
  final TransformLogger logger;
  final Resolver resolver;
  final AssetId outputId;

  static const List<String> _angularAnnotationNames = const [
    'angular.core.annotation_src.NgAttr',
    'angular.core.annotation_src.NgOneWay',
    'angular.core.annotation_src.NgOneWayOneTime',
    'angular.core.annotation_src.NgTwoWay',
    'angular.core.annotation_src.NgCallback'
  ];

  static const Map<String, String> _annotationToMapping = const {
    'NgAttr': '@',
    'NgOneWay': '=>',
    'NgOneWayOneTime': '=>!',
    'NgTwoWay': '<=>',
    'NgCallback': '&',
  };

  ClassElement directiveType;
  ClassElement formatterType;

  /// Resolved annotations that this will pick up for members.
  final List<Element> _annotationElements = <Element>[];

  AnnotationExtractor(this.logger, this.resolver, this.outputId) {
    for (var annotation in _angularAnnotationNames) {
      var type = resolver.getType(annotation);
      if (type == null) {
        logger.warning('Unable to resolve $annotation, skipping metadata.');
        continue;
      }
      _annotationElements.add(type.unnamedConstructor);
    }
    directiveType = resolver.getType('angular.core.annotation_src.Directive');
    formatterType = resolver.getType('angular.core.annotation_src.Formatter');
    if (directiveType == null) {
      logger.warning('Unable to resolve Directive, skipping member annotations.');
    }
    if (formatterType == null) {
      logger.warning('Unable to resolve Formatter.');
    }
  }

  /// Extracts all of the annotations for the specified class.
  AnnotatedType extractAnnotations(ClassElement cls) {
    var classElement = cls;
    var visitor = new _AnnotationVisitor(_annotationElements);
    while (classElement != null) {
      if (resolver.getImportUri(classElement.library, from: outputId) == null) {
        warn('Dropping annotations for ${classElement.name} because the '
            'containing file cannot be imported (must be in a lib folder).', classElement);
        return null;
      }
      if (classElement.node != null) {
        classElement.node.accept(visitor);
      }

      if (classElement.supertype != null) {
        visitor.visitingSupertype = true;
        classElement = classElement.supertype.element;
      } else {
        classElement = null;
      }
    }

    if (!visitor.hasAnnotations) return null;

    var type = new AnnotatedType(cls);
    type.annotations = visitor.classAnnotations
        .where((Annotation annotation) {
          var element = annotation.element;
          if (element != null && !element.isPublic) {
            warn('Annotation $annotation is not public.', cls);
            return false;
          }
          if (element is! ConstructorElement) {
            // Only keeping constructor elements.
            return false;
          }
          ConstructorElement ctor = element;
          var annotationClass = ctor.enclosingElement;
          if (!annotationClass.isPublic) {
            warn('Annotation $annotation is not public.', cls);
            return false;
          }
          return element.enclosingElement.type.isAssignableTo(directiveType.type) ||
                 element.enclosingElement.type.isAssignableTo(formatterType.type);
        }).toList();

    if (type.annotations.isEmpty) return null;

    var memberAnnotations = {};
    visitor.memberAnnotations.forEach((memberName, annotations) {
      if (annotations.length > 1) {
        warn('$memberName can only have one annotation.',
            annotations[0].parent.element);
        return;
      }

      memberAnnotations[memberName] = annotations[0];
    });

    if (memberAnnotations.isNotEmpty) {
      _foldMemberAnnotations(memberAnnotations, type);
    }

    return type;
  }

  /// Folds all AttrFieldAnnotations into the Directive annotation on the
  /// class.
  void _foldMemberAnnotations(Map<String, Annotation> memberAnnotations,
      AnnotatedType type) {
    // Filter down to Directive constructors.
    var ngAnnotations = type.annotations.where((a) {
      var element = a.element;
      if (element is! ConstructorElement) return false;
      return element.enclosingElement.type.isAssignableTo(
          directiveType.type);
    });

    var mapType = resolver.getType('dart.core.Map').type;
    // Find acceptable constructors- ones which take a param named 'map'
    var acceptableAnnotations = ngAnnotations.where((a) {
      var ctor = a.element;

      for (var param in ctor.parameters) {
        if (param.parameterKind != ParameterKind.NAMED) {
          continue;
        }
        if (param.name == 'map' && param.type.isAssignableTo(mapType)) {
          return true;
        }
      }
      return false;
    });

    if (acceptableAnnotations.isEmpty) {
      warn('Could not find a constructor for member annotations in '
          '$ngAnnotations', type.type);
      return;
    }

    // Merge attribute annotations in all of the class annotations
    acceptableAnnotations.forEach((srcAnnotation) {
      // Clone the annotation so we don't modify the one in the persistent AST.
      var index = type.annotations.indexOf(srcAnnotation);
      var annotation = new AstCloner().visitAnnotation(srcAnnotation);
      ResolutionCopier.copyResolutionData(srcAnnotation, annotation);
      type.annotations[index] = annotation;

      var mapArg = annotation.arguments.arguments.firstWhere(
          (arg) => (arg is NamedExpression) && (arg.name.label.name == 'map'),
          orElse: () => null);

      // If we don't have a 'map' parameter yet, add one.
      if (mapArg == null) {
        var map = new MapLiteral(null, null, null, [], null);
        var label = new Label(new SimpleIdentifier(
            new _GeneratedToken(TokenType.STRING, 'map')),
        new _GeneratedToken(TokenType.COLON, ':'));
        mapArg = new NamedExpression(label, map);
        annotation.arguments.arguments.add(mapArg);
      }

      var map = mapArg.expression;
      if (map is! MapLiteral) {
        warn('Expected \'map\' argument of $annotation to be a map literal',
             type.type);
        return;
      }
      memberAnnotations.forEach((memberName, annotation) {
        var key = annotation.arguments.arguments.first;
        // If the key already exists then it means we have two annotations for
        // same member.
        if (map.entries.any((entry) => entry.key.toString() == key.toString())) {
          warn('Directive $annotation already contains an entry for $key',
               type.type);
          return;
        }

        var typeName = annotation.element.enclosingElement.name;
        var value = '${_annotationToMapping[typeName]}$memberName';
        var entry = new MapLiteralEntry(
            key,
            new _GeneratedToken(TokenType.COLON, ':'),
            new SimpleStringLiteral(stringToken(value), value));
        map.entries.add(entry);
      });
    });
  }

  Token stringToken(String str) =>
      new _GeneratedToken(TokenType.STRING, '\'$str\'');

  void warn(String msg, Element element) {
    logger.warning(msg, asset: resolver.getSourceAssetId(element),
        span: resolver.getSourceSpan(element));
  }
}

/// Subclass for tokens which we're generating here.
class _GeneratedToken extends Token {
  final String lexeme;
  _GeneratedToken(TokenType type, this.lexeme) : super(type, 0);
}


/**
 * AST visitor which walks the current AST and finds all annotated
 * classes and members.
 */
class _AnnotationVisitor extends GeneralizingAstVisitor {
  final List<Element> allowedMemberAnnotations;
  final List<Annotation> classAnnotations = [];
  final Map<String, List<Annotation>> memberAnnotations = {};
  var visitingSupertype = false;

  _AnnotationVisitor(this.allowedMemberAnnotations);

  void visitAnnotation(Annotation annotation) {
    var parent = annotation.parent;
    if (parent is! Declaration) return;

    if (parent.element is ClassElement && !visitingSupertype) {
      classAnnotations.add(annotation);

    } else if (allowedMemberAnnotations.contains(annotation.element)) {
      if (parent is MethodDeclaration) {
        memberAnnotations.putIfAbsent(parent.name.name, () => [])
            .add(annotation);
      } else if (parent is FieldDeclaration) {
        var name = parent.fields.variables.first.name.name;
        memberAnnotations.putIfAbsent(name, () => []).add(annotation);
      }
    }
  }

  bool get hasAnnotations =>
      classAnnotations.isNotEmpty || memberAnnotations.isNotEmpty;
}
