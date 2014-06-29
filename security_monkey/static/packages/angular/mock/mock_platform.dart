part of angular.mock;

/**
 * The mock platform exists to smooth out browser differences for tests that
 * do not wish to take browser variance into account. This mock, for most cases,
 * will cause tests to behave according to the most recent spec.
 */
class MockWebPlatform implements WebPlatform {
  bool get cssShimRequired => false;
  bool get shadowDomShimRequired => false;

  String shimCss(String css, { String selector, String cssUrl }) {
    return css;
  }

  void shimShadowDom(Element root, String selector) {}
}