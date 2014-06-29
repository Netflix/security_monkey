/**
 * Core functionality for [angular.dart](#angular/angular), a web framework for Dart.
 *
 * This library is included as part of [angular.dart](#angular/angular). The angular.core library
 * provides all of the fundamental Classes and Type Definitions that provide the basis for
 * formatters (in [angular .formatter](#angular-formatter)) and directives (in [angular.directive]
 * (#angular-directive)).
 *
 */
library angular.core;

export "package:angular/change_detection/watch_group.dart" show
    ReactionFn;

export "package:angular/core/parser/parser.dart" show
    Parser;

export "package:angular/core/parser/dynamic_parser.dart" show
    ClosureMap;

export "package:angular/change_detection/change_detection.dart" show
    AvgStopwatch,
    FieldGetterFactory;

export "package:angular/core_dom/module_internal.dart" show
    Animation,
    AnimationResult,
    BrowserCookies,
    Cache,
    Compiler,
    Cookies,
    BoundViewFactory,
    DirectiveMap,
    ElementProbe,
    EventHandler,
    Http,
    HttpBackend,
    HttpDefaultHeaders,
    HttpDefaults,
    HttpInterceptor,
    HttpInterceptors,
    HttpResponse,
    HttpResponseConfig,
    LocationWrapper,
    NgAnimate,
    NgElement,
    NoOpAnimation,
    NullTreeSanitizer,
    Animate,
    RequestErrorInterceptor,
    RequestInterceptor,
    Response,
    ResponseError,
    UrlRewriter,
    TemplateCache,
    View,
    ViewCache,
    ViewFactory,
    ViewPort;

export "package:angular/core/module_internal.dart" show
    CacheStats,
    ComponentCssRewriter,
    ExceptionHandler,
    Interpolate,
    VmTurnZone,
    WebPlatform,
    PrototypeMap,
    RootScope,
    Scope,
    ScopeDigestTTL,
    ScopeEvent,
    ScopeStats,
    ScopeStatsConfig,
    ScopeStatsEmitter,
    Watch;
