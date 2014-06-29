part of angular.core.dom_internal;


/**
 * BoundViewFactory is a [ViewFactory] which does not need Injector because
 * it is pre-bound to an injector from the parent. This means that this
 * BoundViewFactory can only be used from within a specific Directive such
 * as [NgRepeat], but it can not be stored in a cache.
 *
 * The BoundViewFactory needs [Scope] to be created.
 */
class BoundViewFactory {
  ViewFactory viewFactory;
  Injector injector;

  BoundViewFactory(this.viewFactory, this.injector);

  static Key _SCOPE_KEY = new Key(Scope);

  View call(Scope scope) =>
      viewFactory(injector.createChild([new Module()..bindByKey(_SCOPE_KEY, toValue: scope)]));
}

abstract class ViewFactory implements Function {
  BoundViewFactory bind(Injector injector);

  View call(Injector injector, [List<dom.Node> elements]);
}

/**
 * [WalkingViewFactory] is used to create new [View]s. WalkingViewFactory is
 * created by the [Compiler] as a result of compiling a template.
 */
class WalkingViewFactory implements ViewFactory {
  final List<ElementBinderTreeRef> elementBinders;
  final List<dom.Node> templateElements;
  final Profiler _perf;
  final Expando _expando;

  WalkingViewFactory(this.templateElements, this.elementBinders, this._perf,
                     this._expando) {
    assert(elementBinders.every((ElementBinderTreeRef eb) =>
        eb is ElementBinderTreeRef));
  }

  BoundViewFactory bind(Injector injector) =>
      new BoundViewFactory(this, injector);

  View call(Injector injector, [List<dom.Node> nodes]) {
    if (nodes == null) nodes = cloneElements(templateElements);
    var timerId;
    try {
      assert((timerId = _perf.startTimer('ng.view')) != false);
      var view = new View(nodes, injector.get(EventHandler));
      _link(view, nodes, elementBinders, injector);
      return view;
    } finally {
      assert(_perf.stopTimer(timerId) != false);
    }
  }

  View _link(View view, List<dom.Node> nodeList, List elementBinders,
             Injector parentInjector) {

    var preRenderedIndexOffset = 0;
    var directiveDefsByName = {};

    for (int i = 0; i < elementBinders.length; i++) {
      // querySelectorAll('.ng-binding') should return a list of nodes in the
      // same order as the elementBinders list.

      // keep a injector array --

      var eb = elementBinders[i];
      int index = eb.offsetIndex;

      ElementBinderTree tree = eb.subtree;

      //List childElementBinders = eb.childElementBinders;
      int nodeListIndex = index + preRenderedIndexOffset;
      dom.Node node = nodeList[nodeListIndex];
      var binder = tree.binder;

      var timerId;
      try {
        assert((timerId = _perf.startTimer('ng.view.link', _html(node))) != false);
        // if node isn't attached to the DOM, create a parent for it.
        var parentNode = node.parentNode;
        var fakeParent = false;
        if (parentNode == null) {
          fakeParent = true;
          parentNode = new dom.DivElement()..append(node);
        }

        var childInjector = binder != null ?
            binder.bind(view, parentInjector, node) :
            parentInjector;

        if (fakeParent) {
          // extract the node from the parentNode.
          nodeList[nodeListIndex] = parentNode.nodes[0];
        }

        if (tree.subtrees != null) {
          _link(view, node.nodes, tree.subtrees, childInjector);
        }
      } finally {
        assert(_perf.stopTimer(timerId) != false);
      }
    }
    return view;
  }
}

/**
 * ViewCache is used to cache the compilation of templates into [View]s.
 * It can be used synchronously if HTML is known or asynchronously if the
 * template HTML needs to be looked up from the URL.
 */
@Injectable()
class ViewCache {
  // _viewFactoryCache is unbounded
  final viewFactoryCache = new LruCache<String, ViewFactory>();
  final Http http;
  final TemplateCache templateCache;
  final Compiler compiler;
  final dom.NodeTreeSanitizer treeSanitizer;

  ViewCache(this.http, this.templateCache, this.compiler, this.treeSanitizer);

  ViewFactory fromHtml(String html, DirectiveMap directives) {
    ViewFactory viewFactory = viewFactoryCache.get(html);
    if (viewFactory == null) {
      var div = new dom.DivElement();
      div.setInnerHtml(html, treeSanitizer: treeSanitizer);
      viewFactory = compiler(div.nodes, directives);
      viewFactoryCache.put(html, viewFactory);
    }
    return viewFactory;
  }

  async.Future<ViewFactory> fromUrl(String url, DirectiveMap directives) {
    return http.get(url, cache: templateCache).then(
        (resp) => fromHtml(resp.responseText, directives));
  }
}

class _AnchorAttrs extends NodeAttrs {
  DirectiveRef _directiveRef;

  _AnchorAttrs(DirectiveRef this._directiveRef): super(null);

  String operator [](name) => name == '.' ? _directiveRef.value : null;

  void observe(String attributeName, _AttributeChanged notifyFn) {
    notifyFn(attributeName == '.' ? _directiveRef.value : null);
  }
}

String _html(obj) {
  if (obj is String) {
    return obj;
  }
  if (obj is List) {
    return (obj as List).map((e) => _html(e)).join();
  }
  if (obj is dom.Element) {
    var text = (obj as dom.Element).outerHtml;
    return text.substring(0, text.indexOf('>') + 1);
  }
  return obj.nodeName;
}

/**
 * [ElementProbe] is attached to each [Element] in the DOM. Its sole purpose is
 * to allow access to the [Injector], [Scope], and Directives for debugging and
 * automated test purposes. The information here is not used by Angular in any
 * way.
 *
 * see: [ngInjector], [ngScope], [ngDirectives]
 */
class ElementProbe {
  final ElementProbe parent;
  final dom.Node element;
  final Injector injector;
  final Scope scope;
  final directives = [];

  ElementProbe(this.parent, this.element, this.injector, this.scope);
}
