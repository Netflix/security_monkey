library angular.core.dom_internal;

import 'dart:async' as async;
import 'dart:convert' show JSON;
import 'dart:html' as dom;
import 'dart:js' as js;

import 'package:di/di.dart';
import 'package:perf_api/perf_api.dart';

import 'package:angular/core/annotation.dart';
import 'package:angular/core/annotation_src.dart' show SHADOW_DOM_INJECTOR_NAME;
import 'package:angular/core/module_internal.dart';
import 'package:angular/core/parser/parser.dart';
import 'package:angular/core_dom/dom_util.dart' as util;

import 'package:angular/change_detection/watch_group.dart' show Watch, PrototypeMap;
import 'package:angular/core/registry.dart';

import 'package:angular/directive/module.dart' show NgBaseCss;

part 'animation.dart';
part 'view.dart';
part 'view_factory.dart';
part 'cookies.dart';
part 'common.dart';
part 'compiler.dart';
part 'directive.dart';
part 'directive_map.dart';
part 'element_binder.dart';
part 'element_binder_builder.dart';
part 'event_handler.dart';
part 'http.dart';
part 'mustache.dart';
part 'node_cursor.dart';
part 'web_platform.dart';
part 'selector.dart';
part 'shadow_dom_component_factory.dart';
part 'shadowless_shadow_root.dart';
part 'tagging_compiler.dart';
part 'tagging_view_factory.dart';
part 'template_cache.dart';
part 'transcluding_component_factory.dart';
part 'tree_sanitizer.dart';
part 'walking_compiler.dart';
part 'ng_element.dart';
part 'static_keys.dart';

class CoreDomModule extends Module {
  CoreDomModule() {
    bind(dom.Window, toValue: dom.window);
    bind(ElementProbe, toValue: null);

    // Default to a unlimited-sized TemplateCache
    bind(TemplateCache, toFactory: (_) => new TemplateCache());
    bind(dom.NodeTreeSanitizer, toImplementation: NullTreeSanitizer);

    bind(TextMustache);
    bind(AttrMustache);

    bind(Compiler, toImplementation: TaggingCompiler);

    bind(ComponentFactory, toImplementation: ShadowDomComponentFactory);
    bind(ShadowDomComponentFactory);
    bind(TranscludingComponentFactory);
    bind(Content);
    bind(ContentPort, toValue: null);
    bind(ComponentCssRewriter);
    bind(WebPlatform);
    
    bind(Http);
    bind(UrlRewriter);
    bind(HttpBackend);
    bind(HttpDefaultHeaders);
    bind(HttpDefaults);
    bind(HttpInterceptors);
    bind(Animate);
    bind(ViewCache);
    bind(BrowserCookies);
    bind(Cookies);
    bind(LocationWrapper);
    bind(DirectiveMap);
    bind(DirectiveSelectorFactory);
    bind(ElementBinderFactory);
    bind(NgElement);
    bind(EventHandler);
  }
}
