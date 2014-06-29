library angular.template_cache_annotation;

/**
 * Annotation which will control the caching behavior of objects in the
 * template_cache.
 *
 * Primary use cases are:
 *   - Adding URLs to the cache which cannot be automatically gathered from
 *   Component annotations.
 *   - Adding annotation to an Component to remove it from the template cache.
 */
class NgTemplateCache {
  // List of strings to add to the template cache.
  final List<String> preCacheUrls;
  // Whether to cache these resources in the template cache. Primary use is to
  // override the default caching behavior for Component annotation.
  final bool cache;

  const NgTemplateCache(
      {this.preCacheUrls : const <String> [], this.cache : true});
}
