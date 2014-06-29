part of angular.core.dom_internal;

@proxy
class ShadowlessShadowRoot implements dom.ShadowRoot {
  dom.Element _element;

  ShadowlessShadowRoot(this._element);

  noSuchMethod(Invocation invocation) {
    throw new UnimplementedError("Not yet implemented in ShadowlessShadowRoot.");
  }
}
