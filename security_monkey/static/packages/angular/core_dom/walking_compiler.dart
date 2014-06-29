part of angular.core.dom_internal;

@Injectable()
class WalkingCompiler implements Compiler {
  final Profiler _perf;
  final Expando _expando;

  WalkingCompiler(this._perf, this._expando);

  List<ElementBinderTreeRef> _compileView(NodeCursor domCursor, NodeCursor templateCursor,
                                          ElementBinder existingElementBinder,
                                          DirectiveMap directives) {
    if (domCursor.current == null) return null;

    // don't pre-create to create sparse tree and prevent GC pressure.
    List<ElementBinderTreeRef> elementBinders = null;

    do {
      var subtrees, binder;

      ElementBinder elementBinder;
      if (existingElementBinder != null) {
        elementBinder = existingElementBinder;
      } else {
        var node = domCursor.current;
        switch(node.nodeType) {
          case dom.Node.ELEMENT_NODE:
            elementBinder = directives.selector.matchElement(node);
            break;
          case dom.Node.TEXT_NODE:
            elementBinder = directives.selector.matchText(node);
            break;
          case dom.Node.COMMENT_NODE:
            elementBinder = directives.selector.matchComment(node);
            break;
          default:
            throw "Unknown node type ${node.nodeType}";
        }
      }

      if (elementBinder.hasTemplate) {
        var templateBinder = elementBinder as TemplateElementBinder;
        templateBinder.templateViewFactory = _compileTransclusion(
            domCursor, templateCursor,
            templateBinder.template, templateBinder.templateBinder, directives);
      }

      if (elementBinder.shouldCompileChildren) {
        if (domCursor.descend()) {
          templateCursor.descend();

          subtrees = _compileView(domCursor, templateCursor, null, directives);

          domCursor.ascend();
          templateCursor.ascend();
        }
      }

      if (elementBinder.hasDirectivesOrEvents) {
        binder = elementBinder;
      }

      if (elementBinders == null) elementBinders = [];
      elementBinders.add(new ElementBinderTreeRef(templateCursor.index,
          new ElementBinderTree(binder, subtrees)));
    } while (templateCursor.moveNext() && domCursor.moveNext());

    return elementBinders;
  }

  WalkingViewFactory _compileTransclusion(
      NodeCursor domCursor, NodeCursor templateCursor,
      DirectiveRef directiveRef,
      ElementBinder transcludedElementBinder,
      DirectiveMap directives) {
    var anchorName = directiveRef.annotation.selector +
        (directiveRef.value != null ? '=' + directiveRef.value : '');
    var viewFactory;
    var views;

    var transcludeCursor = templateCursor.replaceWithAnchor(anchorName);
    var domCursorIndex = domCursor.index;
    var elementBinders = _compileView(domCursor, transcludeCursor,
        transcludedElementBinder, directives);
    if (elementBinders == null) elementBinders = [];

    viewFactory = new WalkingViewFactory(transcludeCursor.elements,
        elementBinders, _perf, _expando);
    domCursor.index = domCursorIndex;

    domCursor.replaceWithAnchor(anchorName);

    return viewFactory;
  }

  WalkingViewFactory call(List<dom.Node> elements, DirectiveMap directives) {
    var timerId;
    assert((timerId = _perf.startTimer('ng.compile', _html(elements))) != false);
    final List<dom.Node> domElements = elements;
    final List<dom.Node> templateElements = cloneElements(domElements);
    var elementBinders = _compileView(
        new NodeCursor(domElements), new NodeCursor(templateElements),
        null, directives);

    var viewFactory = new WalkingViewFactory(templateElements,
    elementBinders == null ? [] : elementBinders, _perf, _expando);

    assert(_perf.stopTimer(timerId) != false);
    return viewFactory;
  }
}
