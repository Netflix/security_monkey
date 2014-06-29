part of angular.core.dom_internal;

@Injectable()
class UrlRewriter {
  String call(url) => url;
}

/**
 * HTTP backend used by the [Http] service that delegates to dart:html's
 * [HttpRequest] and deals with Dart bugs.
 *
 * Never use this service directly, instead use the higher-level [Http].
 *
 * During testing this implementation is swapped with [MockHttpBackend] which
 * can be trained with responses.
 */
@Injectable()
class HttpBackend {
  /**
   * Wrapper around dart:html's [HttpRequest.request]
   */
  async.Future request(String url,
      {String method, bool withCredentials, String responseType,
      String mimeType, Map<String, String> requestHeaders, sendData,
      void onProgress(dom.ProgressEvent e)}) =>
      dom.HttpRequest.request(url, method: method,
        withCredentials: withCredentials, responseType: responseType,
        mimeType: mimeType, requestHeaders: requestHeaders,
        sendData: sendData, onProgress: onProgress);
}

@Injectable()
class LocationWrapper {
  get location => dom.window.location;
}

typedef RequestInterceptor(HttpResponseConfig);
typedef RequestErrorInterceptor(dynamic);
typedef Response(HttpResponse);
typedef ResponseError(dynamic);

/**
* HttpInterceptors are used to modify the Http request. They can be added to
* [HttpInterceptors] or passed into [Http.call].
*/
class HttpInterceptor {
  RequestInterceptor request;
  Response response;
  RequestErrorInterceptor requestError;
  ResponseError responseError;

  /**
   * All parameters are optional.
   */
  HttpInterceptor({this.request, this.response, this.requestError,
                  this.responseError});
}


/**
* The default transform data interceptor.abstract
*
* For requests, this interceptor will
* automatically stringify any non-string non-file objects.
*
* For responses, this interceptor will unwrap JSON objects and
* parse them into [Map]s.
*/
class DefaultTransformDataHttpInterceptor implements HttpInterceptor {
  Function request = (HttpResponseConfig config) {
    if (config.data != null && config.data is! String &&
        config.data is! dom.File) {
      config.data = JSON.encode(config.data);
    }
    return config;
  };

  static var _JSON_START = new RegExp(r'^\s*(\[|\{[^\{])');
  static var _JSON_END = new RegExp(r'[\}\]]\s*$');
  static var _PROTECTION_PREFIX = new RegExp('^\\)\\]\\}\',?\\n');
  Function response = (HttpResponse r) {
    if (r.data is String) {
      var d = r.data.replaceFirst(_PROTECTION_PREFIX, '');
      if (d.contains(_JSON_START) && d.contains(_JSON_END)) {
        d = JSON.decode(d);
      }
      return new HttpResponse.copy(r, data: d);
    }
    return r;
  };

  Function requestError, responseError;
}

/**
 * A list of [HttpInterceptor]s.
 */
@Injectable()
class HttpInterceptors {
  List<HttpInterceptor> _interceptors =
      [new DefaultTransformDataHttpInterceptor()];

  add(HttpInterceptor x) => _interceptors.add(x);
  addAll(List<HttpInterceptor> x) => _interceptors.addAll(x);

  /**
   * Called from [Http] to construct a [Future] chain.
   */
  constructChain(List chain) {
    _interceptors.reversed.forEach((HttpInterceptor i) {
      // AngularJS has an optimization of not including null interceptors.
      chain
          ..insert(0, [
              i.request == null ? (x) => x : i.request,
              i.requestError])
          ..add([
              i.response == null ? (x) => x : i.response,
              i.responseError]);
    });
  }

 /**
   * Default constructor.
   */
  HttpInterceptors() {
    _interceptors = [new DefaultTransformDataHttpInterceptor()];
  }

  /**
   * Creates a [HttpInterceptors] from a [List].  Does not include the default
   * interceptors.
   */
  HttpInterceptors.of([List interceptors]) {
    _interceptors = interceptors;
  }
}

/**
 * The request configuration of the request associated with this response.
 */
class HttpResponseConfig {
  /**
   * The request's URL
   */
  String url;

  /**
   * The request params as a Map
   */
  Map params;

  /**
   * The header map without mangled keys
   */
  Map headers;

  var data;
  var _headersObj;

  /**
   * Header accessor. Given a string, it will return the matching header,
   * case-insentivitively. Without a string, returns a header object with
   * lower-case keys.
   */
  header([String name]) {
    if (_headersObj == null) {
      _headersObj = {};
      headers.forEach((k,v) => _headersObj[k.toLowerCase()] = v);
    }

    return name != null ? _headersObj[name.toLowerCase()] : _headersObj;
  }

  /**
   * Constructor
   */
  HttpResponseConfig({this.url, this.params, this.headers, this.data});
}

/**
 * The response for an HTTP request.  Returned from the [Http] service.
 */
class HttpResponse {
  /**
   * The HTTP status code.
   */
  int status;

  /**
   * DEPRECATED
   */
  var responseText;
  Map _headers;

  /**
   * The [HttpResponseConfig] object which contains the requested URL
   */
  HttpResponseConfig config;

  /**
   * Constructor
   */
  HttpResponse([this.status, this.responseText, this._headers, this.config]);

  /**
   * Copy constructor.  Creates a clone of the response, optionally with new
   * data.
   */
  HttpResponse.copy(HttpResponse r, {data}) {
    status = r.status;
    responseText = data == null ? r.responseText : data;
    _headers = r._headers == null ? null : new Map.from(r._headers);
    config = r.config;
  }

  /**
   * The response's data.  Either a string or a transformed object.
   */
  get data => responseText;

  /**
   * The response's headers.  Without parameters, this method will return the
   * [Map] of headers.  With [key] parameter, this method will return the
   * specific header.
   */
  headers([String key]) => key == null ? _headers : _headers[key];

  /**
   * Useful for debugging.
   */
  toString() => 'HTTP $status: $data';
}

/**
 * Default header configuration.
 */
@Injectable()
class HttpDefaultHeaders {
  static var _defaultContentType = 'application/json;charset=utf-8';
  var _headers = {
    'COMMON': {'Accept': 'application/json, text/plain, */*'},
    'POST' : {'Content-Type': _defaultContentType},
    'PUT' : {'Content-Type': _defaultContentType },
    'PATCH' : {'Content-Type': _defaultContentType}
  };

  _applyHeaders(method, ucHeaders, headers) {
    if (!_headers.containsKey(method)) return;
    _headers[method].forEach((k, v) {
      if (!ucHeaders.contains(k.toUpperCase())) {
        headers[k] = v;
      }
    });
  }

  /**
   * Called from [Http], this method sets default headers on [headers]
   */
  setHeaders(Map<String, String> headers, String method) {
    assert(headers != null);
    var ucHeaders = headers.keys.map((x) => x.toUpperCase()).toSet();
    _applyHeaders('COMMON', ucHeaders, headers);
    _applyHeaders(method.toUpperCase(), ucHeaders, headers);
  }

  /**
   * Returns the default header [Map] for a method.  You can then modify
   * the map.
   *
   * Passing 'common' as [method] will return a Map that contains headers
   * common to all operations.
   */
  operator[](method) => _headers[method.toUpperCase()];
}

/**
* Injected into the [Http] service.  This class contains application-wide
* HTTP defaults.
*
* The default implementation provides headers which the
* Angular team believes to be useful.
*/
@Injectable()
class HttpDefaults {
  /**
   * The [HttpDefaultHeaders] object used by [Http] to add default headers
   * to requests.
   */
  HttpDefaultHeaders headers;

  /**
   * The default cache.  To enable caching application-wide, instantiate with a
   * [Cache] object.
   */
  var cache;

  /**
   * The default XSRF cookie name. May not be null.
   */
  String xsrfCookieName = 'XSRF-TOKEN';

  /**
   * The default XSRF header name sent with the request. May not be null.
   */
  String xsrfHeaderName = 'X-XSRF-TOKEN';

  /**
   * Constructor intended for DI.
   */
  HttpDefaults(this.headers);
}

/**
 * The [Http] service facilitates communication with the remote HTTP servers.
 * It uses dart:html's [HttpRequest] and provides a number of features on top
 * of the core Dart library.
 *
 * For unit testing, applications should use the [MockHttpBackend] service.
 *
 * # General usage
 * The [call] method takes a number of named parameters and returns a
 * [Future<HttpResponse>].
 *
 *      http(method: 'GET', url: '/someUrl')
 *        .then((HttpResponse response) { .. },
 *              onError: (HttpRequest request) { .. });
 *
 * A response status code between 200 and 299 is considered a success status and
 * will result in the 'then' being called. Note that if the response is a
 * redirect, Dart's [HttpRequest] will transparently follow it, meaning that the
 * error callback will not be called for such responses.
 *
 * # Shortcut methods
 *
 * The Http service also defines a number of shortcuts:
 *
 *      http.get('/someUrl') is the same as http(method: 'GET', url: '/someUrl')
 *
 * See the method definitions below.
 *
 * # Setting HTTP Headers
 *
 * The [Http] service will add certain HTTP headers to requests.  These defaults
 * can be configured using the [HttpDefaultHeaders] object.  The defaults are:
 *
 * - For all requests: `Accept: application/json, text/plain, * / *`
 * - For POST, PUT, PATCH requests: `Content-Type: application/json`
 *
 * # Caching
 *
 * To enable caching, pass a [Cache] object into the [call] method.  The [Http]
 * service will store responses in the cache and return the response for
 * any matching requests.
 *
 * Note that data is returned through a [Future], regardless of whether it
 * came from the [Cache] or the server.
 *
 * If there are multiple GET requests for the same not-yet-in-cache URL
 * while a cache is in use, only one request to the server will be made.
 *
 * # Interceptors
 *
 * Http uses the interceptors from [HttpInterceptors]. You can also include
 * interceptors in the [call] method.
 *
 * # Security Considerations
 *
 * NOTE: < not yet documented >
 */
@Injectable()
class Http {
  var _pendingRequests = <String, async.Future<HttpResponse>>{};
  BrowserCookies _cookies;
  LocationWrapper _location;
  UrlRewriter _rewriter;
  HttpBackend _backend;
  HttpInterceptors _interceptors;

  /**
   * The defaults for [Http]
   */
  HttpDefaults defaults;

  /**
   * Constructor, useful for DI.
   */
  Http(this._cookies, this._location, this._rewriter, this._backend,
       this.defaults, this._interceptors);

  /**
   * Parse a [requestUrl] and determine whether this is a same-origin request as
   * the application document.
   */
  bool _urlIsSameOrigin(String requestUrl) {
    Uri originUrl = Uri.parse(_location.location.href);
    Uri parsed = originUrl.resolve(requestUrl);
    return (parsed.scheme == originUrl.scheme && parsed.host == originUrl.host);
  }

/**
  * Returns a [Future<HttpResponse>] when the request is fulfilled.
  *
  * Named Parameters:
  * - method: HTTP method (e.g. 'GET', 'POST', etc)
  * - url: Absolute or relative URL of the resource being requested.
  * - data: Data to be sent as the request message data.
  * - params: Map of strings or objects which will be turned to
  *          `?key1=value1&key2=value2` after the url. If the values are
  *           not strings, they will be JSONified.
  * - headers: Map of strings or functions which return strings representing
  *      HTTP headers to send to the server. If the return value of a function
  *      is null, the header will not be sent.
  * - withCredentials: True if cross-site requests should use credentials such as cookies or
  *      authorization headers; false otherwise. If not specified, defaults to false.
  * - xsrfHeaderName: TBI
  * - xsrfCookieName: TBI
  * - interceptors: Either a [HttpInterceptor] or a [HttpInterceptors]
  * - cache: Boolean or [Cache].  If true, the default cache will be used.
  * - timeout: deprecated
*/
  async.Future<HttpResponse> call({
    String url,
    String method,
    data,
    Map<String, dynamic> params,
    Map<String, dynamic> headers,
    bool withCredentials: false,
    xsrfHeaderName,
    xsrfCookieName,
    interceptors,
    cache,
    timeout
  }) {
    if (timeout != null) {
      throw ['timeout not implemented'];
    }

    url = _rewriter(url);
    method = method.toUpperCase();

    if (headers == null) headers = {};
    defaults.headers.setHeaders(headers, method);

    var xsrfValue = _urlIsSameOrigin(url) ?
        _cookies[xsrfCookieName != null ? xsrfCookieName : defaults.xsrfCookieName] :
        null;
    if (xsrfValue != null) {
      headers[xsrfHeaderName != null ? xsrfHeaderName : defaults.xsrfHeaderName]
          = xsrfValue;
    }

    // Check for functions in headers
    headers.forEach((k, v) {
      if (v is Function) headers[k] = v();
    });

    var serverRequest = (HttpResponseConfig config) {
      assert(config.data == null || config.data is String || config.data is dom.File);

      // Strip content-type if data is undefined
      if (config.data == null) {
        new List.from(headers.keys)
            .where((h) => h.toUpperCase() == 'CONTENT-TYPE')
            .forEach((h) => headers.remove(h));
      }

      url = _buildUrl(config.url, config.params);

      if (cache == false) {
        cache = null;
      } else if (cache == null) {
        cache = defaults.cache;
      }

      // We return a pending request only if caching is enabled.
      if (cache != null && _pendingRequests.containsKey(url)) {
        return _pendingRequests[url];
      }
      var cachedResponse = (cache != null && method == 'GET') ? cache.get(url) : null;
      if (cachedResponse != null) {
        return new async.Future.value(new HttpResponse.copy(cachedResponse));
      }

      var result = _backend.request(url,
                                    method: method,
                                    requestHeaders: config.headers,
                                    sendData: config.data,
                                    withCredentials: withCredentials).then((dom.HttpRequest value) {
        // TODO: Uncomment after apps migrate off of this class.
        // assert(value.status >= 200 && value.status < 300);

        var response = new HttpResponse(value.status, value.responseText,
            parseHeaders(value), config);

        if (cache != null) cache.put(url, response);
        _pendingRequests.remove(url);
        return response;
      }, onError: (error) {
        if (error is! dom.ProgressEvent) throw error;
        dom.ProgressEvent event = error;
        _pendingRequests.remove(url);
        dom.HttpRequest request = event.currentTarget;
        return new async.Future.error(
            new HttpResponse(request.status, request.response, parseHeaders(request), config));
      });
      return _pendingRequests[url] = result;
    };

    var chain = [[serverRequest, null]];

    var future = new async.Future.value(new HttpResponseConfig(
        url: url,
        params: params,
        headers: headers,
        data: data));

    _interceptors.constructChain(chain);

    if (interceptors != null) {
      if (interceptors is HttpInterceptor) {
        interceptors = new HttpInterceptors.of([interceptors]);
      }
      assert(interceptors is HttpInterceptors);
      interceptors.constructChain(chain);
    }

    chain.forEach((chainFns) {
      future = future.then(chainFns[0], onError: chainFns[1]);
    });

    return future;
  }

  /**
   * Shortcut method for GET requests.  See [call] for a complete description
   * of parameters.
   */
  async.Future<HttpResponse> get(String url, {
    String data,
    Map<String, dynamic> params,
    Map<String, String> headers,
    bool withCredentials: false,
    xsrfHeaderName,
    xsrfCookieName,
    interceptors,
    cache,
    timeout
  }) => call(method: 'GET', url: url, data: data, params: params, headers: headers,
             withCredentials: withCredentials, xsrfHeaderName: xsrfHeaderName,
             xsrfCookieName: xsrfCookieName, interceptors: interceptors, cache: cache,
             timeout: timeout);

  /**
   * Shortcut method for DELETE requests.  See [call] for a complete description
   * of parameters.
   */
  async.Future<HttpResponse> delete(String url, {
    String data,
    Map<String, dynamic> params,
    Map<String, String> headers,
    bool withCredentials: false,
    xsrfHeaderName,
    xsrfCookieName,
    interceptors,
    cache,
    timeout
  }) => call(method: 'DELETE', url: url, data: data, params: params, headers: headers,
             withCredentials: withCredentials, xsrfHeaderName: xsrfHeaderName,
             xsrfCookieName: xsrfCookieName, interceptors: interceptors, cache: cache,
             timeout: timeout);

  /**
   * Shortcut method for HEAD requests.  See [call] for a complete description
   * of parameters.
   */
  async.Future<HttpResponse> head(String url, {
    String data,
    Map<String, dynamic> params,
    Map<String, String> headers,
    bool withCredentials: false,
    xsrfHeaderName,
    xsrfCookieName,
    interceptors,
    cache,
    timeout
  }) => call(method: 'HEAD', url: url, data: data, params: params, headers: headers,
             withCredentials: withCredentials, xsrfHeaderName: xsrfHeaderName,
             xsrfCookieName: xsrfCookieName, interceptors: interceptors, cache: cache,
             timeout: timeout);

  /**
   * Shortcut method for PUT requests.  See [call] for a complete description
   * of parameters.
   */
  async.Future<HttpResponse> put(String url, String data, {
    Map<String, dynamic> params,
    Map<String, String> headers,
    bool withCredentials: false,
    xsrfHeaderName,
    xsrfCookieName,
    interceptors,
    cache,
    timeout
  }) => call(method: 'PUT', url: url, data: data, params: params, headers: headers,
             withCredentials: withCredentials, xsrfHeaderName: xsrfHeaderName,
             xsrfCookieName: xsrfCookieName, interceptors: interceptors, cache: cache,
             timeout: timeout);

  /**
   * Shortcut method for POST requests.  See [call] for a complete description
   * of parameters.
   */
  async.Future<HttpResponse> post(String url, String data, {
    Map<String, dynamic> params,
    Map<String, String> headers,
    bool withCredentials: false,
    xsrfHeaderName,
    xsrfCookieName,
    interceptors,
    cache,
    timeout
  }) => call(method: 'POST', url: url, data: data, params: params, headers: headers,
             withCredentials: withCredentials, xsrfHeaderName: xsrfHeaderName,
             xsrfCookieName: xsrfCookieName, interceptors: interceptors, cache: cache,
             timeout: timeout);

  /**
   * Shortcut method for JSONP requests.  See [call] for a complete description
   * of parameters.
   */
  async.Future<HttpResponse> jsonp(String url, {
    String data,
    Map<String, dynamic> params,
    Map<String, String> headers,
    bool withCredentials: false,
    xsrfHeaderName,
    xsrfCookieName,
    interceptors,
    cache,
    timeout
  }) => call(method: 'JSONP', url: url, data: data, params: params, headers: headers,
             withCredentials: withCredentials, xsrfHeaderName: xsrfHeaderName,
             xsrfCookieName: xsrfCookieName, interceptors: interceptors, cache: cache,
             timeout: timeout);

  /**
   * Parse raw headers into key-value object
   */
  static Map<String, String> parseHeaders(dom.HttpRequest value) {
    var headers = value.getAllResponseHeaders();

    var parsed = {};

    if (headers == null) return parsed;

    headers.split('\n').forEach((line) {
      var i = line.indexOf(':');
      if (i == -1) return;
      var key = line.substring(0, i).trim().toLowerCase();

      if (key.isNotEmpty) {
        var val = line.substring(i + 1).trim();
        parsed[key] = parsed.containsKey(key) ? "${parsed[key]}, $val" : val;
      }
    });
    return parsed;
  }
  /**
   * Returns an [Iterable] of [Future] [HttpResponse]s for the requests
   * that the [Http] service is currently waiting for.
   */
  Iterable<async.Future<HttpResponse> > get pendingRequests =>
      _pendingRequests.values;

  _buildUrl(String url, Map<String, dynamic> params) {
    if (params == null) return url;
    var parts = [];

    new List.from(params.keys)..sort()..forEach((String key) {
      var value = params[key];
      if (value == null) return;
      if (value is! List) value = [value];

      value.forEach((v) {
        if (v is Map) v = JSON.encode(v);
        parts.add(_encodeUriQuery(key) + '=' + _encodeUriQuery("$v"));
      });
    });
    return url + ((url.indexOf('?') == -1) ? '?' : '&') + parts.join('&');
  }

  _encodeUriQuery(val, {bool pctEncodeSpaces: false}) =>
      Uri.encodeComponent(val)
          .replaceAll('%40', '@')
          .replaceAll('%3A', ':')
          .replaceAll('%24', r'$')
          .replaceAll('%2C', ',')
          .replaceAll('%20', pctEncodeSpaces ? '%20' : '+');
}
