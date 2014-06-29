/**
 * Library for using a pub transformer to automatically switch between
 * dynamic and static injection.
 *
 * ## Step 1: Hook up the build step
 * Edit ```pubspec.yaml``` to add the di transformer to the list of
 * transformers.
 *
 *     name: transformer_demo
 *     version: 0.0.1
 *     dependencies:
 *       di: any
 *       inject: any
 *     transformers:
 *     - di:
 *         dart_entry: web/main.dart
 *         injectable_annotations: transformer_demo.Injectable
 *
 * ## Step 2: Annotate your types
 *
 *     class Engine {
 *       @inject
 *       Engine();
 *     }
 *
 * or
 *
 *     @Injectable // custom annotation specified in pubspec.yaml
 *     class Car {}
 *
 *
 * ## Step 3: Use the auto injector
 * Modify your entry script to use [defaultInjector] as the injector.
 *
 * This must be done from the file registered as the dart_entry in pubspec.yaml
 * as this is the only file which will be modified to include the generated
 * injector.
 *
 *     import 'package:di/auto_injector' as auto;
 *     main() {
 *       var injector = auto.defaultInjector(modules: ...);
 *     }
 }
 */
library di.auto_injector;

import 'package:di/di.dart';
import 'package:di/dynamic_injector.dart';

@MirrorsUsed(override: '*')
import 'dart:mirrors' show MirrorsUsed;

Injector defaultInjector({List<Module> modules, String name,
    bool allowImplicitInjection: false}) =>
    new DynamicInjector(
      modules: modules,
      name: name,
      allowImplicitInjection: allowImplicitInjection);
