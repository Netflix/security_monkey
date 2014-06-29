part of angular.core.dom_internal;

/**
 * Infinite cache service for templates loaded from URLs.
 *
 * All templates that are loaded from a URL are cached indefinitely in the
 * TemplateCache the first time they are needed.  This includes templates loaded
 * via `ng-include` or via the `templateUrl` field on components decorated with
 * [Component].
 *
 * All attempts that require loading a template from a URL are first checked
 * against this cache.  Only when there is a cache miss is a network request
 * attempted.
 *
 * You are welcome to pre-load / seed the TemplateCache with templates for URLs
 * in advance to avoid the network hit on first load.
 *
 * There are two ways to seed the TemplateCache:
 * 1. imperatively via and the `TemplateCache` service
 * 2. declaratively in HTML via both `<template type=text/ng-template>` and
 *    `<script type=text/ng-template>` tags (handled by [NgTemplate])
 *
 * Here is an example that illustrates both techniques
 * ([view in plunker](http://plnkr.co/edit/JCsxhH?p=info)):
 *
 * Example:
 *
 *     // main.dart
 *     import 'package:angular/angular.dart';
 *     import 'package:angular/application_factory.dart';
 *
 *     @Directive(selector: '[load-template-cache]')
 *     class LoadTemplateCacheDirective {
 *       LoadTemplateCacheDirective(TemplateCache templateCache, Scope scope) {
 *         // Method 1 (imperative): Via the injected TemplateCache service.
 *         templateCache.put('template_1.html',
 *                           new HttpResponse(200, 't1: My name is {{name}}.'));
 *         scope.context["name"] = "chirayu";
 *       }
 *     }
 *
 *     main() {
 *       applicationFactory()
 *           .addModule(new Module()..bind(LoadTemplateCacheDirective))
 *           .run();
 *     }
 *
 * and
 *
 *     <!-- index.html -->
 *     <html>
 *       <head>
 *         <script src="packages/browser/dart.js"></script>
 *         <script src="main.dart" type="application/dart"></script>
 *
 *         <!-- Method 2 (declarative): Via the template directive. -->
 *         <template id="template_2.html" type="text/ng-template">
 *           t2: My name is {{name}}.
 *         </template>
 *       </head>
 *       <body load-template-cache>
 *         template_1.html: <div ng-include="'template_1.html'"></div><br>
 *         template_2.html: <div ng-include="'template_2.html'"></div><br>
 *       </body>
 *     </html>
 *
 * Neither `ng-include` above will result in a network hit.  This means that it
 * isn't necessary for your web server to even serve those templates.
 */
class TemplateCache extends LruCache<String, HttpResponse> {
  TemplateCache({int capacity}): super(capacity: capacity);
}
