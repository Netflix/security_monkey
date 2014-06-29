library di.dynamic_injector;

import 'di.dart';
import 'src/mirrors.dart';
import 'src/base_injector.dart';
import 'src/error_helper.dart';
import 'src/provider.dart';

export 'di.dart';

/**
 * Dynamic implementation of [Injector] that uses mirrors.
 */
class DynamicInjector extends BaseInjector {

  DynamicInjector({List<Module> modules, String name,
                  bool allowImplicitInjection: false})
      : super(modules: modules, name: name,
          allowImplicitInjection: allowImplicitInjection);

  DynamicInjector._fromParent(List<Module> modules, Injector parent, {name})
      : super.fromParent(modules, parent, name: name);

  newFromParent(List<Module> modules, String name) =>
      new DynamicInjector._fromParent(modules, this, name: name);

  Object newInstanceOf(Type type, ObjectFactory objFactory, Injector requestor,
                       resolving) {
    var classMirror = reflectType(type);
    if (classMirror is TypedefMirror) {
      throw new NoProviderError(error(resolving, 'No implementation provided '
          'for ${getSymbolName(classMirror.qualifiedName)} typedef!'));
    }

    MethodMirror ctor = classMirror.declarations[classMirror.simpleName];

    if (ctor == null) {
      throw new NoProviderError('Unable to find default constructor for $type. '
          'Make sure class has a default constructor.' + (1.0 is int ?
              'Make sure you have correctly configured @MirrorsUsed.' : ''));
    }

    resolveArgument(int pos) {
      ParameterMirror p = ctor.parameters[pos];
      if (p.type.qualifiedName == #dynamic) {
        var name = MirrorSystem.getName(p.simpleName);
        throw new NoProviderError(
            error(resolving, "The '$name' parameter must be typed"));
      }
      if (p.type is TypedefMirror) {
        throw new NoProviderError(
            error(resolving,
                  'Cannot create new instance of a typedef ${p.type}'));
      }
      if (p.metadata.isNotEmpty) {
        assert(p.metadata.length == 1);
        var type = p.metadata.first.type.reflectedType;
        return objFactory.getInstanceByKey(
            new Key((p.type as ClassMirror).reflectedType, type),
            requestor, resolving);
      } else {
        return objFactory.getInstanceByKey(
            new Key((p.type as ClassMirror).reflectedType),
            requestor, resolving);
      }
    }

    var args = new List.generate(ctor.parameters.length, resolveArgument,
        growable: false);
    return classMirror.newInstance(ctor.constructorName, args).reflectee;
  }

  /**
   * Invoke given function and inject all its arguments.
   *
   * Returns whatever the function returns.
   */
  dynamic invoke(Function fn) {
    ClosureMirror cm = reflect(fn);
    MethodMirror mm = cm.function;
    int position = 0;
    List args = mm.parameters.map((ParameterMirror parameter) {
      try {
        if (parameter.metadata.isNotEmpty) {
          var annotation = parameter.metadata[0].type.reflectedType;
          return get((parameter.type as ClassMirror).reflectedType, annotation);
        } else {
          return get((parameter.type as ClassMirror).reflectedType);
        }
      } on NoProviderError catch (e) {
        throw new NoProviderError(e.message);
      } finally {
        position++;
      }
    }).toList();

    return cm.apply(args).reflectee;
  }
}
