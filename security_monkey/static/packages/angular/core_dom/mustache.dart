part of angular.core.dom_internal;

// This Directive is special and does not go through injection.
@Decorator(selector: r':contains(/{{.*}}/)')
class TextMustache {
  final dom.Node _element;

  TextMustache(this._element,
                          String template,
                          Interpolate interpolate,
                          Scope scope,
                          FormatterMap formatters) {
    String expression = interpolate(template);

    scope.watch(expression,
                _updateMarkup,
                canChangeModel: false,
                formatters: formatters);
  }

  void _updateMarkup(text, previousText) {
    _element.text = text;
  }
}

// This Directive is special and does not go through injection.
@Decorator(selector: r'[*=/{{.*}}/]')
class AttrMustache {
  bool _hasObservers;
  Watch _watch;
  NodeAttrs _attrs;
  String _attrName;

  // This Directive is special and does not go through injection.
  AttrMustache(this._attrs,
                          String template,
                          Interpolate interpolate,
                          Scope scope,
                          FormatterMap formatters) {
    var eqPos = template.indexOf('=');
    _attrName = template.substring(0, eqPos);
    String expression = interpolate(template.substring(eqPos + 1));

    _updateMarkup('', template);

    _attrs.listenObserverChanges(_attrName, (hasObservers) {
    if (_hasObservers != hasObservers) {
      _hasObservers = hasObservers;
      if (_watch != null) _watch.remove();
        _watch = scope.watch(expression, _updateMarkup, formatters: formatters,
            canChangeModel: _hasObservers);
      }
    });
  }

  void _updateMarkup(text, previousText) {
    if (text != previousText && !(previousText == null && text == '')) {
        _attrs[_attrName] = text;
    }
  }
}

