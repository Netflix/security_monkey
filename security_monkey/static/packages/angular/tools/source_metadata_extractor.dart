library angular.source_metadata_extractor ;

import 'package:analyzer/src/generated/ast.dart';
import 'package:angular/tools/source_crawler.dart';
import 'package:angular/tools/common.dart';

const String _COMPONENT = '-component';
const String _DIRECTIVE = '-directive';
String _ATTR_DIRECTIVE = '-attr' + _DIRECTIVE;
RegExp _ATTR_SELECTOR_REGEXP = new RegExp(r'\[([^\]]+)\]');
const List<String> _specs = const ['=>!', '=>', '<=>', '@', '&'];
const Map<String, String> _attrAnnotationsToSpec = const {
  'NgAttr': '@',
  'NgOneWay': '=>',
  'NgOneWayOneTime': '=>!',
  'NgTwoWay': '<=>',
  'NgCallback': '&'
};

class SourceMetadataExtractor {
  DirectiveMetadataCollectingVisitor metadataVisitor;

  SourceMetadataExtractor([ this.metadataVisitor ]) {
    if (metadataVisitor == null) {
      metadataVisitor = new DirectiveMetadataCollectingVisitor();
    }
  }

  List<DirectiveInfo> gatherDirectiveInfo(root, SourceCrawler sourceCrawler) {
    sourceCrawler.crawl(root, metadataVisitor);

    List<DirectiveInfo> directives = <DirectiveInfo>[];
    metadataVisitor.metadata.forEach((DirectiveMetadata meta) {
      DirectiveInfo dirInfo = new DirectiveInfo();
      dirInfo.selector = meta.selector;
      dirInfo.template = meta.template;
      meta.attributeMappings.forEach((attrName, mappingSpec) {
        var spec = _specs
            .firstWhere((specPrefix) => mappingSpec.startsWith(specPrefix),
                orElse: () => throw '$mappingSpec no matching spec');
        if (spec != '@') {
          dirInfo.expressionAttrs.add(attrName);
        }
        if (mappingSpec.length == 1) { // Shorthand. Remove.
          // TODO(pavelgj): Figure out if short-hand LHS should be expanded
          // and added to the expressions list.
          if (attrName != '.') {
            dirInfo.expressions.add(attrName);
          }
        } else {
          mappingSpec = mappingSpec.substring(spec.length);
          if (mappingSpec.startsWith('.')) {
            mappingSpec = mappingSpec.substring(1);
          }
          dirInfo.expressions.add(mappingSpec);
        }
      });

      meta.exportExpressionAttrs.forEach((attr) {
        if (!dirInfo.expressionAttrs.contains(attr)) {
          dirInfo.expressionAttrs.add(attr);
        }
      });

      meta.exportExpressions.forEach((expr) {
        if (!dirInfo.expressions.contains(expr)) {
          dirInfo.expressions.add(expr);
        }
      });


      // No explicit selector specified on the directive, compute one.
      var className = meta.className;
      if (dirInfo.selector == null) {
        if (meta.type == COMPONENT) {
          if (className.endsWith(_COMPONENT)) {
            dirInfo.selector = className.
                substring(0, className.length - _COMPONENT.length);
          } else {
            throw "Directive name '$className' must end with $_DIRECTIVE, "
            "$_ATTR_DIRECTIVE, $_COMPONENT or have a \$selector field.";
          }
        } else {
          if (className.endsWith(_ATTR_DIRECTIVE)) {
            var attrName = className.
                substring(0, className.length - _ATTR_DIRECTIVE.length);
            dirInfo.selector = '[$attrName]';
          } else if (className.endsWith(_DIRECTIVE)) {
            dirInfo.selector = className.
                substring(0, className.length - _DIRECTIVE.length);
          } else {
            throw "Directive name '$className' must have a \$selector field.";
          }
        }
      }
      var reprocessedAttrs = <String>[];
      dirInfo.expressionAttrs.forEach((String attr) {
        if (attr == '.') {
          var matches = _ATTR_SELECTOR_REGEXP.allMatches(dirInfo.selector);
          if (matches.isNotEmpty) {
            reprocessedAttrs.add(matches.last.group(1));
          }
        } else {
          reprocessedAttrs.add(attr);
        }
      });
      dirInfo.expressionAttrs = reprocessedAttrs;
      directives.add(dirInfo);
    });

    directives.addAll(metadataVisitor.templates.map(
        (tmpl) => new DirectiveInfo()..template = tmpl));

    return directives;
  }
}

class DirectiveMetadataCollectingAstVisitor extends RecursiveAstVisitor {
  final List<DirectiveMetadata> metadata;
  final List<String> templates;

  DirectiveMetadataCollectingAstVisitor(this.metadata, this.templates);

  visitMethodInvocation(MethodInvocation node) {
    if (node.methodName.name == 'ngRoute') {
      NamedExpression viewHtmlExpression =
          node.argumentList.arguments
          .firstWhere((e) => e is NamedExpression &&
              e.name.label.name == 'viewHtml', orElse: () => null);
      if (viewHtmlExpression != null) {
        if (viewHtmlExpression.expression is! StringLiteral) {
          throw 'viewHtml must be a string literal';
        }
        templates.add(
            (viewHtmlExpression.expression as StringLiteral).stringValue);
      }
    }
    super.visitMethodInvocation(node);
  }

  visitClassDeclaration(ClassDeclaration clazz) {
    // Check class annotations for presense of Component/Decorator.
    clazz.metadata.forEach((Annotation ann) {
      if (ann.arguments == null) return; // Ignore non-class annotations.
      // TODO(pavelj): this is not a safe check for the type of the
      // annotations, but good enough for now.
      if (ann.name.name != 'Component'
          && ann.name.name != 'Decorator') return;

      bool isComponent = ann.name.name == 'Component';

      var meta = new DirectiveMetadata()
        ..className = clazz.name.name
        ..type = isComponent ? COMPONENT : DIRECTIVE;
      metadata.add(meta);

      ann.arguments.arguments.forEach((Expression arg) {
        if (arg is NamedExpression) {
          NamedExpression namedArg = arg;
          var paramName = namedArg.name.label.name;
          if (paramName == 'selector') {
            meta.selector = assertString(namedArg.expression).stringValue;
          }
          if (paramName == 'template') {
            meta.template = assertString(namedArg.expression).stringValue;
          }
          if (paramName == 'map') {
            MapLiteral map = namedArg.expression;
            map.entries.forEach((MapLiteralEntry entry) {
              meta.attributeMappings[assertString(entry.key).stringValue] =
                  assertString(entry.value).stringValue;
            });
          }
          if (paramName == 'exportExpressions') {
            meta.exportExpressions = getStringValues(namedArg.expression);
          }
          if (paramName == 'exportExpressionAttrs') {
            meta.exportExpressionAttrs = getStringValues(namedArg.expression);
          }
        }
      });

      if (meta != null) _walkSuperclassChain(clazz, meta, _extractMappingsFromClass);
    });

    return super.visitClassDeclaration(clazz);
  }

  _walkSuperclassChain(ClassDeclaration clazz, DirectiveMetadata meta,
                       metadataExtractor(ClassDeclaration clazz, DirectiveMetadata meta)) {
    while (clazz != null) {
      metadataExtractor(clazz, meta);
      if (clazz.element != null && clazz.element.supertype != null) {
        clazz = clazz.element.supertype.element.node;
      } else {
        clazz = null;
      }
    }
  }

  _extractMappingsFromClass(ClassDeclaration clazz, DirectiveMetadata meta) {
    // Check fields/getters/setter for presence of attr mapping annotations.
    clazz.members.forEach((ClassMember member) {
      if (member is FieldDeclaration ||
      (member is MethodDeclaration &&
      (member.isSetter || member.isGetter))) {
        member.metadata.forEach((Annotation ann) {
          if (_attrAnnotationsToSpec.containsKey(ann.name.name)) {
            String fieldName;
            if (member is FieldDeclaration) {
              fieldName = member.fields.variables.first.name.name;
            } else { // MethodDeclaration
              fieldName = (member as MethodDeclaration).name.name;
            }
            StringLiteral attNameLiteral = ann.arguments.arguments.first;
            if (meta.attributeMappings
            .containsKey(attNameLiteral.stringValue)) {
              throw 'Attribute mapping already defined for '
              '${clazz.name}.$fieldName';
            }
            meta.attributeMappings[attNameLiteral.stringValue] =
            _attrAnnotationsToSpec[ann.name.name] + fieldName;
          }
        });
      }
    });
  }
}

class DirectiveMetadataCollectingVisitor {
  List<DirectiveMetadata> metadata = <DirectiveMetadata>[];
  List<String> templates = <String>[];

  call(CompilationUnit cu) {
    cu.accept(new DirectiveMetadataCollectingAstVisitor(metadata, templates));
  }
}

List<String> getStringValues(ListLiteral listLiteral) {
  List<String> res = <String>[];
  for (Expression element in listLiteral.elements) {
    res.add(assertString(element).stringValue);
  }
  return res;
}

StringLiteral assertString(Expression key) {
  if (key is! StringLiteral) {
    throw 'must be a string literal: ${key.runtimeType}';
  }
  return key;
}
