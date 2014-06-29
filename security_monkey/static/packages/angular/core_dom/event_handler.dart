part of angular.core.dom_internal;

typedef void EventFunction(event);

/**
 * [EventHandler] is responsible for handling events bound using on-* syntax
 * (i.e. `on-click="ctrl.doSomething();"`). The root of the application has an
 * EventHandler attached as does every [Component].
 *
 * Events bound within [Component] are handled by EventHandler attached to
 * their [ShadowRoot]. All other events are handled by EventHandler attached
 * to the application root ([Application]).
 *
 * **Note**: The expressions are executed within the closest context.
 *
 * Example:
 *
 *     <div foo>
 *       <button on-click="ctrl.say('Hello');">Button</button>;
 *     </div>
 *
 *     @Component(selector: '[foo]', publishAs: ctrl)
 *     class FooController {
 *       say(String something) => print(something);
 *     }
 *
 * When button is clicked, "Hello" will be printed in the console.
 */
@Injectable()
class EventHandler {
  dom.Node _rootNode;
  final Expando _expando;
  final ExceptionHandler _exceptionHandler;
  final _listeners = <String, Function>{};

  EventHandler(this._rootNode, this._expando, this._exceptionHandler);

  /**
   * Register an event. This makes sure that  an event (of the specified name)
   * which bubbles to this node, gets processed by this [EventHandler].
   */
  void register(String eventName) {
    _listeners.putIfAbsent(eventName, () {
      dom.EventListener eventListener = this._eventListener;
      _rootNode.on[eventName].listen(eventListener);
      return eventListener;
    });
  }

  void _eventListener(dom.Event event) {
    dom.Node element = event.target;
    while (element != null && element != _rootNode) {
      var expression;
      if (element is dom.Element)
        expression = (element as dom.Element).attributes[eventNameToAttrName(event.type)];
      if (expression != null) {
        try {
          var scope = _getScope(element);
          if (scope != null) scope.eval(expression);
        } catch (e, s) {
          _exceptionHandler(e, s);
        }
      }
      element = element.parentNode;
    }
  }

  Scope _getScope(dom.Node element) {
    // var topElement = (rootNode is dom.ShadowRoot) ? rootNode.parentNode : rootNode;
    while (element != _rootNode.parentNode) {
      ElementProbe probe = _expando[element];
      if (probe != null) {
        return probe.scope;
      }
      element = element.parentNode;
    }
    return null;
  }

  /**
  * Converts event name into attribute. Event named 'someCustomEvent' needs to
  * be transformed into on-some-custom-event.
  */
  static String eventNameToAttrName(String eventName) {
    var part = eventName.replaceAllMapped(new RegExp("([A-Z])"), (Match match) {
      return '-${match.group(0).toLowerCase()}';
    });
    return 'on-${part}';
  }

  /**
  * Converts attribute into event name. Attribute 'on-some-custom-event'
  * corresponds to event named 'someCustomEvent'.
  */
  static String attrNameToEventName(String attrName) {
    var part = attrName.startsWith("on-") ? attrName.substring(3) : attrName;
    part = part.replaceAllMapped(new RegExp(r'\-(\w)'), (Match match) {
      return match.group(0).toUpperCase();
    });
    return part.replaceAll("-", "");
  }
}

@Injectable()
class ShadowRootEventHandler extends EventHandler {
  ShadowRootEventHandler(dom.ShadowRoot shadowRoot,
                         Expando expando,
                         ExceptionHandler exceptionHandler)
      : super(shadowRoot, expando, exceptionHandler);
}
