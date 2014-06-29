part of angular.core.dom_internal;

@Injectable()
class NullTreeSanitizer implements dom.NodeTreeSanitizer {
  void sanitizeTree(dom.Node node) {}
}
