part of angular.core.dom_internal;

class TaggingViewFactory implements ViewFactory {
  final List<TaggedElementBinder> elementBinders;
  final List<dom.Node> templateNodes;
  final Profiler _perf;

  TaggingViewFactory(this.templateNodes, this.elementBinders, this._perf);

  BoundViewFactory bind(Injector injector) => new BoundViewFactory(this, injector);

  static Key _EVENT_HANDLER_KEY = new Key(EventHandler);

  View call(Injector injector, [List<dom.Node> nodes /* TODO: document fragment */]) {
    if (nodes == null) {
      nodes = cloneElements(templateNodes);
    }
    var timerId;
    try {
      assert((timerId = _perf.startTimer('ng.view')) != false);
      var view = new View(nodes, injector.getByKey(_EVENT_HANDLER_KEY));
      _link(view, nodes, injector);
      return view;
    } finally {
      assert(_perf.stopTimer(timerId) != false);
    }
  }

  void _bindTagged(TaggedElementBinder tagged, int elementBinderIndex, Injector rootInjector,
                   List<Injector> elementInjectors, View view, boundNode) {
    var binder = tagged.binder;
    var parentInjector = tagged.parentBinderOffset == -1 ?
        rootInjector :
        elementInjectors[tagged.parentBinderOffset];
    assert(parentInjector != null);

    var elementInjector = elementInjectors[elementBinderIndex] =
        binder != null ? binder.bind(view, parentInjector, boundNode) : parentInjector;

    if (tagged.textBinders != null) {
      for (var k = 0; k < tagged.textBinders.length; k++) {
        TaggedTextBinder taggedText = tagged.textBinders[k];
        taggedText.binder.bind(view, elementInjector, boundNode.childNodes[taggedText.offsetIndex]);
      }
    }
  }

  View _link(View view, List<dom.Node> nodeList, Injector rootInjector) {
    var elementInjectors = new List<Injector>(elementBinders.length);
    var directiveDefsByName = {};

    var elementBinderIndex = 0;
    for (int i = 0; i < nodeList.length; i++) {
      var node = nodeList[i];

      // if node isn't attached to the DOM, create a parent for it.
      var parentNode = node.parentNode;
      var fakeParent = false;
      if (parentNode == null) {
        fakeParent = true;
        parentNode = new dom.DivElement();
        parentNode.append(node);
      }

      if (node.nodeType == dom.Node.ELEMENT_NODE) {
        var elts = node.querySelectorAll('.ng-binding');
        // querySelectorAll doesn't return the node itself
        if (node.classes.contains('ng-binding')) {
          var tagged = elementBinders[elementBinderIndex];
          _bindTagged(tagged, elementBinderIndex, rootInjector, elementInjectors, view, node);
          elementBinderIndex++;
        }

        for (int j = 0; j < elts.length; j++, elementBinderIndex++) {
          TaggedElementBinder tagged = elementBinders[elementBinderIndex];
          _bindTagged(tagged, elementBinderIndex, rootInjector, elementInjectors, view, elts[j]);
        }
      } else if (node.nodeType == dom.Node.TEXT_NODE ||
                 node.nodeType == dom.Node.COMMENT_NODE) {
        TaggedElementBinder tagged = elementBinders[elementBinderIndex];
        assert(tagged.binder != null || tagged.isTopLevel);
        if (tagged.binder != null) {
          _bindTagged(tagged, elementBinderIndex, rootInjector, elementInjectors, view, node);
        }
        elementBinderIndex++;
      } else {
        throw "nodeType sadness ${node.nodeType}}";
      }

      if (fakeParent) {
        // extract the node from the parentNode.
        nodeList[i] = parentNode.nodes[0];
      }
    }
    return view;
  }
}
