library di.static_injector;

import 'di.dart';
import 'src/error_helper.dart';
import 'src/base_injector.dart';
import 'src/provider.dart';

export 'annotations.dart';
export 'di.dart';

/**
 * Static implementation of [Injector] that uses type factories
 */
class StaticInjector extends BaseInjector {
  Map<Type, TypeFactory> typeFactories;

  StaticInjector({List<Module> modules, String name,
                 bool allowImplicitInjection: false, typeFactories})
      : super(modules: modules, name: name,
          allowImplicitInjection: allowImplicitInjection) {
    this.typeFactories = _extractTypeFactories(modules, typeFactories);
  }

  StaticInjector._fromParent(List<Module> modules, Injector parent, {name})
      : super.fromParent(modules, parent, name: name) {
    this.typeFactories = _extractTypeFactories(modules);
  }

  newFromParent(List<Module> modules, String name) =>
      new StaticInjector._fromParent(modules, this, name: name);

  Object newInstanceOf(Type type, ObjectFactory objFactory,
                       Injector requestor, resolving) {
    TypeFactory typeFactory = _getFactory(type);
    if (typeFactory == null) {
      throw new NoProviderError(
          error(resolving, 'No type factory provided for $type!'));
    }
    return typeFactory((type, [annotation]) =>
        objFactory.getInstanceByKey(
            new Key(type, annotation), requestor, resolving));
  }

  TypeFactory _getFactory(Type key) {
    var cursor = this;
    while (cursor != null) {
      if (cursor.typeFactories.containsKey(key)) {
        return cursor.typeFactories[key];
      }
      cursor = cursor.parent;
    }
    return null;
  }
}

Map<Type, TypeFactory> _extractTypeFactories(List<Module> modules,
    [Map<Type, TypeFactory> initial = const {}]) {
  if (modules == null || modules.isEmpty) return initial;
  var factories = new Map.from(initial == null ? {} : initial);
  modules.forEach((m) {
    factories.addAll(m.typeFactories);
  });
  return factories;
}
