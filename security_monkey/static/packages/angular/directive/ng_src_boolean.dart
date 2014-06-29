part of angular.directive;

/**
 * Allows adding and removing the boolean attributes from the element.
 *
 * Using `<button disabled="{{false}}">` does not work since it would result
 * in `<button disabled="false">` rather than `<button>`.
 * Browsers change behavior based on presence/absence of the attribute rather
 * its value.
 *
 * For this reason we provide alternate `ng-`attribute directives to
 * add/remove boolean attributes such as `<button ng-disabled="{{false}}">`
 * which will result in proper removal of the attribute.
 *
 * The full list of supported attributes are:
 *
 *  - [ng-checked]
 *  - [ng-disabled]
 *  - [ng-multiple]
 *  - [ng-open]
 *  - [ng-readonly]
 *  - [ng-required]
 *  - [ng-selected]
 */
@Decorator(selector: '[ng-checked]',  map: const {'ng-checked':  '=>checked'})
@Decorator(selector: '[ng-disabled]', map: const {'ng-disabled': '=>disabled'})
@Decorator(selector: '[ng-multiple]', map: const {'ng-multiple': '=>multiple'})
@Decorator(selector: '[ng-open]',     map: const {'ng-open':     '=>open'})
@Decorator(selector: '[ng-readonly]', map: const {'ng-readonly': '=>readonly'})
@Decorator(selector: '[ng-required]', map: const {'ng-required': '=>required'})
@Decorator(selector: '[ng-selected]', map: const {'ng-selected': '=>selected'})
class NgBooleanAttribute {
  final NgElement _ngElement;

  NgBooleanAttribute(this._ngElement);

  void set checked(on)  => _toggleAttribute('checked',  on);
  void set disabled(on) => _toggleAttribute('disabled', on);
  void set multiple(on) => _toggleAttribute('multiple', on);
  void set open(on)     => _toggleAttribute('open', on);
  void set readonly(on) => _toggleAttribute('readonly', on);
  void set required(on) => _toggleAttribute('required', on);
  void set selected(on) => _toggleAttribute('selected', on);

  void _toggleAttribute(attrName, on) {
    if (toBool(on)) {
      _ngElement.setAttribute(attrName);
    } else {
      _ngElement.removeAttribute(attrName);
    }
  }
}

/**
 * In browser some attributes have network side-effect. If the attribute
 * has `{{interpolation}}` in it it may cause browser to fetch bogus URLs.
 *
 * Example: In `<img src="{{username}}.png">` the browser will fetch the image
 * `http://server/{{username}}.png` before Angular has a chance to replace the
 * attribute with data-bound url.
 *
 * For this reason we provide `ng-`prefixed attributes which avoid the issues
 * mentioned above as in this example: `<img ng-src="{{username}}.png">`.
 *
 * The full list of supported attributes are:
 *
 * - [ng-href]
 * - [ng-src]
 * - [ng-srcset]
 */
@Decorator(selector: '[ng-href]',   map: const {'ng-href':   '@href'})
@Decorator(selector: '[ng-src]',    map: const {'ng-src':    '@src'})
@Decorator(selector: '[ng-srcset]', map: const {'ng-srcset': '@srcset'})
class NgSource {
  final NgElement _ngElement;
  NgSource(this._ngElement);

  void set href(value)   => _ngElement.setAttribute('href', value);
  void set src(value)    => _ngElement.setAttribute('src', value);
  void set srcset(value) => _ngElement.setAttribute('srcset', value);

}

/**
 * In SVG some attributes have a specific syntax. Placing `{{interpolation}}` in
 * those attributes will break the attribute syntax, and browser will clear the
 * attribute.
 *
 * The `ng-attr-*` is a generic way to use interpolation without breaking the
 * attribute syntax validator. The `ng-attr-` part get stripped.
 *
 * @example
 *     <svg>
 *       <circle ng-attr-cx="{{cx}}"></circle>
 *     </svg>
 */
@Decorator(selector: '[ng-attr-*]')
class NgAttribute implements AttachAware {
  final NodeAttrs _attrs;

  NgAttribute(this._attrs);

  void attach() {
    String ngAttrPrefix = 'ng-attr-';
    _attrs.forEach((key, value) {
      if (key.startsWith(ngAttrPrefix)) {
        var newKey = key.substring(ngAttrPrefix.length);
        _attrs[newKey] = value;
        _attrs.observe(key, (newValue) => _attrs[newKey] = newValue );
      }
    });
  }
}
