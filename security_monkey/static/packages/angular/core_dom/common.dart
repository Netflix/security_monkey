part of angular.core.dom_internal;

List<dom.Node> cloneElements(elements) {
  return elements.map((el) => el.clone(true)).toList();
}

class MappingParts {
  final String attrName;
  final String mode;
  final String dstExpression;
  final String originalValue;

  const MappingParts(this.attrName, this.mode, this.dstExpression, this.originalValue);
}

class DirectiveRef {
  final dom.Node element;
  final Type type;
  final Key typeKey;
  final Directive annotation;
  final String value;
  final mappings = new List<MappingParts>();

  DirectiveRef(this.element, this.type, this.annotation, this.typeKey, [ this.value ]);

  String toString() {
    var html = element is dom.Element
        ? (element as dom.Element).outerHtml
        : element.nodeValue;
    return '{ element: $html, selector: ${annotation.selector}, value: $value, '
           'type: $type }';
  }
}

/**
 * Creates a child injector that allows loading new directives, formatters and
 * services from the provided modules.
 */
Injector forceNewDirectivesAndFormatters(Injector injector, List<Module> modules) {
  modules.add(new Module()
      ..bind(Scope, toFactory: (i) {
        var scope = i.parent.get(Scope);
        return scope.createChild(new PrototypeMap(scope.context));
      }));

  return injector.createChild(modules,
      forceNewInstances: [DirectiveMap, FormatterMap]);
}
