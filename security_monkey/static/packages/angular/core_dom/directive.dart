part of angular.core.dom_internal;

/// Callback function used to notify of attribute changes.
typedef void _AttributeChanged(String newValue);

/// Callback function used to notify of observer changes.
typedef void Mustache(bool hasObservers);

/**
 * NodeAttrs is a facade for element attributes.
 *
 * This facade allows reading and writing the attribute values as well as
 * adding observers triggered when:
 * - The value of an attribute changes,
 * - An element becomes observed.
 */
class NodeAttrs {
  final dom.Element element;

  Map<String, List<_AttributeChanged>> _observers;
  final _mustacheAttrs = <String, _MustacheAttr>{};

  NodeAttrs(this.element);

  operator [](String attrName) => element.attributes[attrName];

  void operator []=(String attrName, String value) {
    if (_mustacheAttrs.containsKey(attrName)) {
      _mustacheAttrs[attrName].isComputed = true;
    }
    if (value == null) {
      element.attributes.remove(attrName);
    } else {
      element.attributes[attrName] = value;
    }

    if (_observers != null && _observers.containsKey(attrName)) {
      _observers[attrName].forEach((notifyFn) => notifyFn(value));
    }
  }

  /**
   * Observes changes to the attribute by invoking the [notifyFn]
   * function. On registration the [notifyFn] function gets invoked in order to
   * synchronize with the current value.
   *
   * When an observed is registered on an attributes any existing
   * [_observerListeners] will be called with the first parameter set to
   * [:true:]
   */
  observe(String attrName, notifyFn(String value)) {
    if (_observers == null) _observers = <String, List<_AttributeChanged>>{};
    _observers.putIfAbsent(attrName, () => <_AttributeChanged>[])
              .add(notifyFn);

    if (_mustacheAttrs.containsKey(attrName)) {
      if (_mustacheAttrs[attrName].isComputed) notifyFn(this[attrName]);
      _mustacheAttrs[attrName].notifyFn(true);
    } else {
      notifyFn(this[attrName]);
    }
  }

  void forEach(void f(String k, String v)) {
    element.attributes.forEach(f);
  }

  bool containsKey(String attrName) => element.attributes.containsKey(attrName);

  Iterable<String> get keys => element.attributes.keys;

  /**
   * Registers a listener to be called when the attribute [attrName] becomes
   * observed. On registration [notifyFn] function gets invoked with [:false:]
   * as the first argument.
   */
  void listenObserverChanges(String attrName, Mustache notifyFn) {
    _mustacheAttrs[attrName] = new _MustacheAttr(notifyFn);
    notifyFn(false);
  }
}

/**
 * [TemplateLoader] is an asynchronous access to ShadowRoot which is
 * loaded asynchronously. It allows a Component to be notified when its
 * ShadowRoot is ready.
 */
class TemplateLoader {
  final async.Future<dom.Node> template;

  TemplateLoader(this.template);
}

class _MustacheAttr {
  // Listener trigger when the attribute becomes observed
  final Mustache notifyFn;
  // Whether the value has first been computed
  bool isComputed = false;

  _MustacheAttr(this.notifyFn);
}
