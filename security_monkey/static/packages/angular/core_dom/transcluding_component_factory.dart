part of angular.core.dom_internal;

@Decorator(
   selector: 'content')
class Content implements AttachAware, DetachAware {
  final ContentPort _port;
  final dom.Element _element;
  dom.Comment _beginComment;
  Content(this._port, this._element);

  void attach() {
    if (_port == null) return;
    _beginComment = _port.content(_element);
  }
  
  void detach() {
    if (_port == null) return;
    _port.detachContent(_beginComment);
  }
}

class ContentPort {
  dom.Element _element;
  var _childNodes = [];

  ContentPort(this._element);

  void pullNodes() {
    _childNodes.addAll(_element.nodes);
    _element.nodes = [];
  }

  content(dom.Element elt) {
    var hash = elt.hashCode;
    var beginComment = null;

    if (_childNodes.isNotEmpty) {
      beginComment = new dom.Comment("content $hash");
      elt.parent.insertBefore(beginComment, elt);
      elt.parent.insertAllBefore(_childNodes, elt);
      elt.parent.insertBefore(new dom.Comment("end-content $hash"), elt);
      _childNodes = [];
    }

    elt.remove();
    return beginComment;
  }

  void detachContent(dom.Comment _beginComment) {
    // Search for endComment and extract everything in between.
    // TODO optimize -- there may be a better way of pulling out nodes.

    if (_beginComment == null) {
      return;
    }

    var endCommentText = "end-${_beginComment.text}";

    var next;
    for (next = _beginComment.nextNode;
         next.nodeType != dom.Node.COMMENT_NODE || next.text != endCommentText;
         next = _beginComment.nextNode) {
      _childNodes.add(next);
      next.remove();
    }
    assert(next.nodeType == dom.Node.COMMENT_NODE && next.text == endCommentText);
    next.remove();
  }
}

@Injectable()
class TranscludingComponentFactory implements ComponentFactory {
  final Expando _expando;

  TranscludingComponentFactory(this._expando);

  FactoryFn call(dom.Node node, DirectiveRef ref) {
    // CSS is not supported.
    assert((ref.annotation as Component).cssUrls == null ||
           (ref.annotation as Component).cssUrls.isEmpty);

    var element = node as dom.Element;
    return (Injector injector) {
      var childInjector;
      var component = ref.annotation as Component;
      Scope scope = injector.get(Scope);
      ViewCache viewCache = injector.get(ViewCache);
      Http http = injector.get(Http);
      TemplateCache templateCache = injector.get(TemplateCache);
      DirectiveMap directives = injector.get(DirectiveMap);
      NgBaseCss baseCss = injector.get(NgBaseCss);

      var contentPort = new ContentPort(element);

      // Append the component's template as children
      var viewFuture = ComponentFactory._viewFuture(component, viewCache, directives);
      var elementFuture;

      if (viewFuture != null) {
        elementFuture = viewFuture.then((ViewFactory viewFactory) {
          contentPort.pullNodes();
          element.nodes.addAll(viewFactory(childInjector).nodes);
          return element;
        });
      } else {
        elementFuture = new async.Future.microtask(() => contentPort.pullNodes());
      }
      TemplateLoader templateLoader = new TemplateLoader(elementFuture);

      Scope shadowScope = scope.createChild({});

      var probe;
      var childModule = new Module()
          ..bind(ref.type)
          ..bind(NgElement)
          ..bind(ContentPort, toValue: contentPort)
          ..bind(Scope, toValue: shadowScope)
          ..bind(TemplateLoader, toValue: templateLoader)
          ..bind(dom.ShadowRoot, toValue: new ShadowlessShadowRoot(element))
          ..bind(ElementProbe, toFactory: (_) => probe);
      childInjector = injector.createChild([childModule], name: SHADOW_DOM_INJECTOR_NAME);

      var controller = childInjector.get(ref.type);
      shadowScope.context[component.publishAs] = controller;
      ComponentFactory._setupOnShadowDomAttach(controller, templateLoader, shadowScope);
      return controller;
    };
  }
}
