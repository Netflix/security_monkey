/**
 * Angular class annotations for Directives, Formatters, and Injectables.
 */
library angular.core.annotation;

import "dart:html" show ShadowRoot;

export "package:angular/core/annotation_src.dart" show
    AttachAware,
    DetachAware,
    ShadowRootAware,

    Formatter,
    Injectable,

    Directive,
    Component,
    Controller,
    Decorator,

    DirectiveAnnotation,
    NgAttr,
    NgCallback,
    NgOneWay,
    NgOneWayOneTime,
    NgTwoWay;


/**
 * Implementing components [onShadowRoot] method will be called when
 * the template for the component has been loaded and inserted into Shadow DOM.
 * It is guaranteed that when [onShadowRoot] is invoked, that shadow DOM
 * has been loaded and is ready.
 */
abstract class ShadowRootAware {
  void onShadowRoot(ShadowRoot shadowRoot);
}

