library di.annotations;

/**
 * Annotation that can be applied to the library declaration listing all
 * types for which type factories should be generated to be used
 * by StaticInjector.
 */
class Injectables {
  final List<Type> types;
  const Injectables(this.types);
}

/**
 * Annotation that can be applied to a class for which type factories
 * should be generated to be used by StaticInjector.
 */
class Injectable {
  const Injectable();
}
