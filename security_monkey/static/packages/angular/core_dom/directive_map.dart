part of angular.core.dom_internal;

@Injectable()
class DirectiveMap extends AnnotationsMap<Directive> {
  DirectiveSelectorFactory _directiveSelectorFactory;
  DirectiveSelector _selector;
  DirectiveSelector get selector {
    if (_selector != null) return _selector;
    return _selector = _directiveSelectorFactory.selector(this);
  }

  DirectiveMap(Injector injector,
               MetadataExtractor metadataExtractor,
               this._directiveSelectorFactory)
      : super(injector, metadataExtractor);
}
