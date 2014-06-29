part of angular.core.dom_internal;

/**
 * Shims for interacting with experimental platform feature that are required
 * for the correct behavior of angular, but are not supported on all browsers
 * without polyfills.
 *
 * http://www.polymer-project.org/docs/polymer/styling.html
 */
@Injectable()
class WebPlatform {
  js.JsObject _platformJs;
  js.JsObject _shadowCss;

  bool get cssShimRequired => _shadowCss != null;
  bool get shadowDomShimRequired => _shadowCss != null;

  WebPlatform() {
    var _platformJs = js.context['Platform'];
    if (_platformJs != null) {
      _shadowCss = _platformJs['ShadowCSS'];

      if (_shadowCss != null) {
        _shadowCss['strictStyling'] = true;
      }
    }
  }

  String shimCss(String css, { String selector, String cssUrl }) {
    if (!cssShimRequired) return css;

    var shimmedCss =  _shadowCss.callMethod('shimCssText', [css, selector]);
    return "/* Shimmed css for <$selector> from $cssUrl */\n$shimmedCss";
  }

  void shimShadowDom(dom.Element root, String selector) {
    if (shadowDomShimRequired) {

      // This adds an empty attribute with the name of the component tag onto
      // each element in the shadow root.
      root.querySelectorAll("*")
          .forEach((n) => n.attributes[selector] = "");
    }
  }
}

class PlatformViewCache implements ViewCache {
  final ViewCache cache;
  final String selector;
  final WebPlatform platform;

  get viewFactoryCache => cache.viewFactoryCache;
  Http get http => cache.http;
  TemplateCache get templateCache => cache.templateCache;
  Compiler get compiler => cache.compiler;
  dom.NodeTreeSanitizer get treeSanitizer => cache.treeSanitizer;

  PlatformViewCache(this.cache, this.selector, this.platform);

  ViewFactory fromHtml(String html, DirectiveMap directives) {
    ViewFactory viewFactory;

    if (selector != null && selector != ""
        && platform.shadowDomShimRequired) {

      // By adding a comment with the tag name we ensure the template html is
      // unique per selector name when used as a key in the view factory
      // cache.
      viewFactory = viewFactoryCache.get(
          "<!-- Shimmed template for: <$selector> -->$html");
    } else {
      viewFactory = viewFactoryCache.get(html);
    }

    if (viewFactory == null) {
      var div = new dom.DivElement();
      div.setInnerHtml(html, treeSanitizer: treeSanitizer);

      if (selector != null && selector != ""
          && platform.shadowDomShimRequired) {
        // This MUST happen before the compiler is called so that every dom
        // element gets touched before the compiler removes them for
        // transcluding directives like ng-if.
        platform.shimShadowDom(div, selector);
      }

      viewFactory = compiler(div.nodes, directives);
      viewFactoryCache.put(html, viewFactory);
    }
    return viewFactory;
  }

  async.Future<ViewFactory> fromUrl(String url, DirectiveMap directives) {
    return http.get(url, cache: templateCache).then(
            (resp) => fromHtml(resp.responseText, directives));
  }
}
