/**
 * Bootstrapping for Angular applications via [app:factory](#angular-app-factory) for development,
 * or [app:factory:static](#angular-app-factory-static) for production.
 *
 * In your `main()` function, you bootstrap Angular by explicitly defining and adding a module for
 * your application:
 *
 *     import 'package:angular/angular.dart';
 *     import 'package:angular/application_factory.dart';
 *
 *     class MyModule extends Module {
 *       MyModule() {
 *         bind(HelloWorldController);
 *       }
 *     }
 *
 *     main() {
 *       applicationFactory()
 *           .addModule(new MyModule())
 *           .run();
 *     }
 *
 * In the code above, we use [applicationFactory](#angular-app-factory) to
 * take advantage of [dart:mirrors]
 * (https://api.dartlang.org/apidocs/channels/stable/dartdoc-viewer/dart-mirrors) during
 * development. When you run the app in Dartium the [app:factory](#angular-app-factory)
 * implementation allows for quick edit-test development cycle.
 *
 * Note that you must explicitly import both `angular.dart` and `application_factory.dart` at
 * the start of your file.
 *
 * For production, transformers defined in your `pubspec.yaml` file convert the code to
 * use the [app:factory:static](#angular-app-factory-static) when you run `pub build`. Instead of
 * relying on mirrors (which disable tree-shaking and thus generate large JS size), the transformers
 * generate getters, setters, annotations, and factories needed by Angular. The result is that
 * `dart2js` can than enable tree-shaking and produce smaller output.
 *
 * To enable the transformers add this rule as shown below to your `pubspec.yaml`:
 *
 *     name: angular_dart_example
 *     version: 0.0.1
 *     dependencies:
 *       angular: '>= 0.9.11'
 *       browser: any
 *       unittest: any
 *
 *     transformers:
 *     - angular
 *
 * If your app structure makes use of directories for storing your templates,
 * you must also specify rules for `html_files` to ensure that the transformers pick up those
 * files. You only need to specify the HTML files; the parser will infer the correct `.dart` and
 * CSS files to include.
 *
 * For example:
 *
 *     transformers:
 *     - angular:
 *         html_files:
 *         - lib/_some_library_/_some_component_.html
 *
 * If you need a way to build your app without transformers, you can use
 * [staticApplicationFactory](#angular-app-factory-static@id_staticApplicationFactory) directly,
 * instead of [applicationFactory](#angular-app-factory@id_dynamicApplication). See the
 * documentation for the [app:factory:static](#angular-app-factory-static) library definition for
 * more on this use case.
 */
library angular.app;

import 'dart:html' as dom;

import 'package:intl/date_symbol_data_local.dart';
import 'package:di/di.dart';
import 'package:angular/angular.dart';
import 'package:angular/perf/module.dart';
import 'package:angular/core/module_internal.dart';
import 'package:angular/core/registry.dart';
import 'package:angular/core_dom/module_internal.dart';
import 'package:angular/directive/module.dart';
import 'package:angular/formatter/module_internal.dart';
import 'package:angular/routing/module.dart';
import 'package:angular/introspection_js.dart';

/**
 * This is the top level module which describes all Angular components,
 * including services, formatters and directives. When instantiating an Angular application
 * through [applicationFactory](#angular-app-factory), AngularModule is automatically included.
 *
 * You can use AngularModule explicitly when creating a custom Injector that needs to know
 * about Angular services, formatters, and directives. When writing tests, this is typically done for
 * you by the [SetUpInjector](#angular-mock@id_setUpInjector) method.
 */
class AngularModule extends Module {
  AngularModule() {
    install(new CoreModule());
    install(new CoreDomModule());
    install(new DirectiveModule());
    install(new FormatterModule());
    install(new PerfModule());
    install(new RoutingModule());

    bind(MetadataExtractor);
    bind(Expando, toValue: elementExpando);
  }
}

/**
 * The Application class provides the mechanism by which Angular creates, configures,
 * and runs an application. There are two implementations for this abstract class:
 *
 * - [app:factory](#angular-app-factory), which is intended for development. In this
 *   mode Angular uses
 *   [dart:mirrors](https://api.dartlang.org/apidocs/channels/stable/dartdoc-viewer/dart-mirrors)
 *   to dynamically generate getters, setters, annotations, and factories at runtime.
 * - [app:factory:static](#angular-app-factory-static) is used as part of `pub
 *   build` by transformers that generate the getters, setters, annotations,
 *   and factories needed by Angular.
 *   Because the code is statically generated, `dart2js` can then use full tree-shaking for
 *   minimal output size.
 *
 * Refer to the documentation for [angular.app](#angular-app) for details of how to use
 * applicationFactory to bootstrap your Angular application.
 *
 */
abstract class Application {
  static _find(String selector, [dom.Element defaultElement]) {
    var element = dom.document.querySelector(selector);
    if (element == null) element = defaultElement;
    if (element == null) {
      throw "Could not find application element '$selector'.";
    }
    return element;
  }

  final VmTurnZone zone = new VmTurnZone();
  final AngularModule ngModule = new AngularModule();
  final List<Module> modules = <Module>[];
  dom.Element element;

  /**
   * Creates a selector for a DOM element.
   */
  dom.Element selector(String selector) => element = _find(selector);

  Application(): element = _find('[ng-app]', dom.window.document.documentElement) {
    modules.add(ngModule);
    ngModule..bind(VmTurnZone, toValue: zone)
            ..bind(Application, toValue: this)
            ..bind(dom.Node, toFactory: (i) => i.get(Application).element);
  }

  /**
   * Returns the injector for this module.
   */
  Injector injector;

  Application addModule(Module module) {
    modules.add(module);
    return this;
  }

  Injector run() {
    publishToJavaScript();
    return zone.run(() {
      var rootElements = [element];
      Injector injector = createInjector();
      ExceptionHandler exceptionHandler = injector.get(ExceptionHandler);
      initializeDateFormatting(null, null).then((_) {
        try {
          var compiler = injector.get(Compiler);
          var viewFactory = compiler(rootElements, injector.get(DirectiveMap));
          viewFactory(injector, rootElements);
        } catch (e, s) {
          exceptionHandler(e, s);
        }
      });
      return injector;
    });
  }

  /**
   * Creates an injector function that can be used for retrieving services as well as for
   * dependency injection.
   */
  Injector createInjector();
}
