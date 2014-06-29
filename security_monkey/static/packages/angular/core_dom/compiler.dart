part of angular.core.dom_internal;

abstract class Compiler implements Function {
  ViewFactory call(List<dom.Node> elements, DirectiveMap directives);
}
