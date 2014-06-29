library angular.tools.common;

class DirectiveInfo {
  String selector;
  String template;
  List<String> expressionAttrs = <String>[];
  List<String> expressions = <String>[];
  DirectiveInfo([this.selector, this.expressionAttrs, this.expressions]) {
    if (expressionAttrs == null) {
      expressionAttrs = <String>[];
    }
    if (expressions == null) {
      expressions = <String>[];
    }
  }
}

const String DIRECTIVE = 'DIRECTIVE';
const String COMPONENT = 'COMPONENT';

class DirectiveMetadata {
  String className;
  String type; // DIRECTIVE/COMPONENT
  String selector;
  String template;
  Map<String, String> attributeMappings;
  List<String> exportExpressionAttrs;
  List<String> exportExpressions;

  DirectiveMetadata([this.className, this.type, this.selector,
                     this.attributeMappings, this.exportExpressionAttrs,
                     this.exportExpressions]) {
    if (attributeMappings == null) {
      attributeMappings = <String, String>{};
    }
    if (exportExpressions == null) {
      exportExpressions = <String>[];
    }
    if (exportExpressionAttrs == null) {
      exportExpressionAttrs = <String>[];
    }
  }
}

