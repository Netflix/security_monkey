library angular.mock.http_backend;

import 'dart:async' as dart_async;
import 'dart:convert' show JSON;
import 'dart:html';

import 'package:angular/angular.dart';
import 'package:angular/utils.dart' as utils;


class _MockXhr {
  var method, url, async, reqHeaders, respHeaders;

  void open(method, url, async) {
    this.method = method;
    this.url = url;
    this.async = async;
    reqHeaders = {};
    respHeaders = {};
  }

  var data;

  void send(data) {
    data = data;
  }

  void setRequestHeader(key, value) {
    reqHeaders[key] = value;
  }

  String getResponseHeader(name) {
    // the lookup must be case insensitive, that's why we try two quick
    // lookups and full scan at last
    if (respHeaders.containsKey(name)) return respHeaders[name];

    name = name.toLowerCase();
    if (respHeaders.containsKey(name)) return respHeaders[name];

    String header = null;
    respHeaders.forEach((headerName, headerVal) {
      if (header != null) return;
      if (headerName.toLowerCase()) header = headerVal;
    });
    return header;
  }

  getAllResponseHeaders() {
    if (respHeaders == null) return '';

    var lines = [];

    respHeaders.forEach((key, value) {
      lines.add("$key: $value");
    });
    return lines.join('\n');
  }

  // noop
  abort() {}
}

/**
 * An internal class used by [MockHttpBackend].
 */
class MockHttpExpectation {
  final String method;
  final /*String or RegExp*/ url;
  final data;
  final headers;
  final bool withCredentials;

  var response;

  MockHttpExpectation(this.method, this.url, [this.data, this.headers, withCredentials]) :
      this.withCredentials = withCredentials == true;

  bool match(method, url, [data, headers, withCredentials]) {
    if (method != method) return false;
    if (!matchUrl(url)) return false;
    if (data != null && !matchData(data)) return false;
    if (headers != null && !matchHeaders(headers)) return false;
    if (withCredentials != null && !matchWithCredentials(withCredentials)) return false;
    return true;
  }

  bool matchUrl(u) {
    if (url == null) return true;
    if (url is RegExp) return url.hasMatch(u);
    return url == u;
  }

  bool matchHeaders(h) {
    if (headers == null) return true;
    if (headers is Function) return headers(h);
    return "$headers" == "$h";
  }

  bool matchData(d) {
    if (data == null) return true;
    if (d == null) return false;
    if (data is File) return data == d;
    assert(d is String);
    if (data is RegExp) return data.hasMatch(d);
    return JSON.encode(data) == JSON.encode(d);
  }

  bool matchWithCredentials(withCredentials) => this.withCredentials == withCredentials;

  String toString() => "$method $url";
}


class _Chain {
  final Function _respondFn;
  _Chain({respond}): _respondFn = respond;
  respond([x,y,z]) => _respondFn(x,y,z);
}

/**
 * A mock implementation of [HttpBackend], used in tests.
 */
class MockHttpBackend implements HttpBackend {
  var definitions = [],
      expectations = [],
      responses = [];

  /**
   * This function is called from [Http] and designed to mimic the Dart APIs.
   */
  dart_async.Future request(String url,
                 {String method, bool withCredentials: false, String responseType,
                 String mimeType, Map<String, String> requestHeaders, sendData,
                 void onProgress(ProgressEvent e)}) {
    dart_async.Completer c = new dart_async.Completer();
    var callback = (status, data, headers) {
      if (status >= 200 && status < 300) {
        c.complete(new MockHttpRequest(status, data, headers));
      } else {
        c.completeError(new MockProgressEvent(
            new MockHttpRequest(status, data, headers)));
      }
    };
    call(method == null ? 'GET' : method, url, callback,
         data: sendData, headers: requestHeaders, withCredentials: withCredentials);
    return c.future;
  }

  _createResponse(statusOrDataOrFunction, dataOrHeaders, headersOrNone) {
    if (statusOrDataOrFunction is Function) return statusOrDataOrFunction;
    var status, data, headers;
    if (statusOrDataOrFunction is num) {
      status = statusOrDataOrFunction;
      data = dataOrHeaders;
      headers = headersOrNone;
    } else {
      status = 200;
      data = statusOrDataOrFunction;
      headers = dataOrHeaders;
    }
    if (data is Map || data is List) data = JSON.encode(data);

    return ([a,b,c,d,e]) => [status, data, headers];
  }


 /**
  * A callback oriented API.  This function takes a callback with
  * will be called with (status, data, headers)
  */
  void call(method, url, callback, {data, headers, timeout, withCredentials: false}) {
    var xhr = new _MockXhr(),
        expectation = expectations.isEmpty ? null : expectations[0],
        wasExpected = false;

    var prettyPrint = (data) {
      return (data is String || data is Function || data is RegExp)
          ? data
          : JSON.encode(data);
    };

    var wrapResponse = (wrapped) {
      var handleResponse = () {
        var response = wrapped.response(method, url, data, headers);
        xhr.respHeaders = response[2];
        utils.relaxFnApply(callback, [response[0], response[1],
             xhr.getAllResponseHeaders()]);
      };

      var handleTimeout = () {
        for (var i = 0; i < responses.length; i++) {
          if (identical(responses[i], handleResponse)) {
            responses.removeAt(i);
            callback(-1, null, '');
            break;
          }
        }
      };

      if (timeout != null) timeout.then(handleTimeout);
      return handleResponse;
    };

    if (expectation != null && expectation.match(method, url)) {
      if (!expectation.matchData(data))
        throw ['Expected $expectation with different data\n' +
            'EXPECTED: ${prettyPrint(expectation.data)}\nGOT:      $data'];

      if (!expectation.matchHeaders(headers))
        throw ['Expected $expectation with different headers\n'
            'EXPECTED: ${prettyPrint(expectation.headers)}\n'
            'GOT:      ${prettyPrint(headers)}'];

      if (!expectation.matchWithCredentials(withCredentials))
        throw ['Expected $expectation with different withCredentials\n'
            'EXPECTED: ${prettyPrint(expectation.withCredentials)}\n'
            'GOT:      ${prettyPrint(withCredentials)}'];

      expectations.removeAt(0);

      if (expectation.response != null) {
        responses.add(wrapResponse(expectation));
        return;
      }
      wasExpected = true;
    }

    for (var definition in definitions) {
      if (definition.match(method, url, data, headers != null ? headers : {}, withCredentials)) {
        if (definition.response != null) {
          // if $browser specified, we do auto flush all requests
          responses.add(wrapResponse(definition));
        } else throw ['No response defined !'];
        return;
      }
    }
    throw wasExpected ?
        ['No response defined !'] :
        ['Unexpected request: $method $url\n' + (expectation != null ?
            'Expected $expectation' :
            'No more requests expected')];
  }

  /**
   * Creates a new backend definition.
   *
   * @param {string} method HTTP method.
   * @param {string|RegExp} url HTTP url.
   * @param {(string|RegExp)=} data HTTP request body.
   * @param {(Object|function(Object))=} headers HTTP headers or function that
   * receives http header object and returns true if the headers match the
   * current definition.
   * @returns {requestHandler} Returns an object with `respond` method that
   * control how a matched request is handled.
   *
   *  - respond – `{function([status,] data[, headers])|function(function(method, url, data, headers)}`
   *    – The respond method takes a set of static data to be returned or a function that can return
   *    an array containing response status (number), response data (string) and response headers
   *    (Object).
   */
  _Chain when(method, [url, data, headers, withCredentials = false]) {
    var definition = new MockHttpExpectation(method, url, data, headers, withCredentials),
        chain = new _Chain(respond: (status, data, headers) {
          definition.response = _createResponse(status, data, headers);
        });

    definitions.add(definition);
    return chain;
  }

  /**
   * @ngdoc method
   * @name ngMock.httpBackend#whenGET
   * @methodOf ngMock.httpBackend
   * @description
   * Creates a new backend definition for GET requests. For more info see `when()`.
   *
   * @param {string|RegExp} url HTTP url.
   * @param {(Object|function(Object))=} headers HTTP headers.
   * @returns {requestHandler} Returns an object with `respond` method that control how a matched
   * request is handled.
   */
  _Chain whenGET(url, [headers]) => when('GET', url, null, headers);

  /**
   * @ngdoc method
   * @name ngMock.httpBackend#whenDELETE
   * @methodOf ngMock.httpBackend
   * @description
   * Creates a new backend definition for DELETE requests. For more info see `when()`.
   *
   * @param {string|RegExp} url HTTP url.
   * @param {(Object|function(Object))=} headers HTTP headers.
   * @returns {requestHandler} Returns an object with `respond` method that control how a matched
   * request is handled.
   */
  _Chain whenDELETE(url, [headers]) => when('DELETE', url, null, headers);

  /**
   * @ngdoc method
   * @name ngMock.httpBackend#whenJSONP
   * @methodOf ngMock.httpBackend
   * @description
   * Creates a new backend definition for JSONP requests. For more info see `when()`.
   *
   * @param {string|RegExp} url HTTP url.
   * @returns {requestHandler} Returns an object with `respond` method that control how a matched
   * request is handled.
   */
  _Chain whenJSONP(url, [headers]) => when('JSONP', url, null, headers);

  /**
   * @ngdoc method
   * @name ngMock.httpBackend#whenPUT
   * @methodOf ngMock.httpBackend
   * @description
   * Creates a new backend definition for PUT requests.  For more info see `when()`.
   *
   * @param {string|RegExp} url HTTP url.
   * @param {(string|RegExp)=} data HTTP request body.
   * @param {(Object|function(Object))=} headers HTTP headers.
   * @returns {requestHandler} Returns an object with `respond` method that control how a matched
   * request is handled.
   */
  _Chain whenPUT(url, [data, headers]) => when('PUT', url, data, headers);

  /**
   * @ngdoc method
   * @name ngMock.httpBackend#whenPOST
   * @methodOf ngMock.httpBackend
   * @description
   * Creates a new backend definition for POST requests. For more info see `when()`.
   *
   * @param {string|RegExp} url HTTP url.
   * @param {(string|RegExp)=} data HTTP request body.
   * @param {(Object|function(Object))=} headers HTTP headers.
   * @returns {requestHandler} Returns an object with `respond` method that control how a matched
   * request is handled.
   */
  _Chain whenPOST(url, [data, headers]) => when('POST', url, data, headers);

  _Chain whenPATCH(url, [data, headers]) => when('PATCH', url, data, headers);

  /**
   * @ngdoc method
   * @name ngMock.httpBackend#whenHEAD
   * @methodOf ngMock.httpBackend
   * @description
   * Creates a new backend definition for HEAD requests. For more info see `when()`.
   *
   * @param {string|RegExp} url HTTP url.
   * @param {(Object|function(Object))=} headers HTTP headers.
   * @returns {requestHandler} Returns an object with `respond` method that control how a matched
   * request is handled.
   */

  /**
   * @ngdoc method
   * @name ngMock.httpBackend#expect
   * @methodOf ngMock.httpBackend
   * @description
   * Creates a new request expectation.
   *
   * @param {string} method HTTP method.
   * @param {string|RegExp} url HTTP url.
   * @param {(string|RegExp)=} data HTTP request body.
   * @param {(Object|function(Object))=} headers HTTP headers or function that receives http header
   *   object and returns true if the headers match the current expectation.
   * @returns {requestHandler} Returns an object with `respond` method that control how a matched
   *  request is handled.
   *
   *  - respond – `{function([status,] data[, headers])|function(function(method, url, data, headers)}`
   *    – The respond method takes a set of static data to be returned or a function that can return
   *    an array containing response status (number), response data (string) and response headers
   *    (Object).
   */
  _Chain expect(method, [url, data, headers, withCredentials = false]) {
    var expectation = new MockHttpExpectation(method, url, data, headers, withCredentials);
    expectations.add(expectation);
    return new _Chain(respond: (status, data, headers) {
      expectation.response = _createResponse(status, data, headers);
    });
  }


  /**
   * @ngdoc method
   * @name ngMock.httpBackend#expectGET
   * @methodOf ngMock.httpBackend
   * @description
   * Creates a new request expectation for GET requests. For more info see `expect()`.
   *
   * @param {string|RegExp} url HTTP url.
   * @param {Object=} headers HTTP headers.
   * @returns {requestHandler} Returns an object with `respond` method that control how a matched
   * request is handled. See #expect for more info.
   */
  _Chain expectGET(url, [headers, withCredentials = false]) => expect('GET', url, null, headers,
      withCredentials);

  /**
   * @ngdoc method
   * @name ngMock.httpBackend#expectDELETE
   * @methodOf ngMock.httpBackend
   * @description
   * Creates a new request expectation for DELETE requests. For more info see `expect()`.
   *
   * @param {string|RegExp} url HTTP url.
   * @param {Object=} headers HTTP headers.
   * @returns {requestHandler} Returns an object with `respond` method that control how a matched
   *   request is handled.
   */
  _Chain expectDELETE(url, [headers, withCredentials = false]) => expect('DELETE', url, null,
      headers, withCredentials);

  /**
   * @ngdoc method
   * @name ngMock.httpBackend#expectJSONP
   * @methodOf ngMock.httpBackend
   * @description
   * Creates a new request expectation for JSONP requests. For more info see `expect()`.
   *
   * @param {string|RegExp} url HTTP url.
   * @returns {requestHandler} Returns an object with `respond` method that control how a matched
   *   request is handled.
   */
  _Chain expectJSONP(url, [headers, withCredentials = false]) => expect('JSONP', url, null, headers,
      withCredentials);

  /**
   * @ngdoc method
   * @name ngMock.httpBackend#expectPUT
   * @methodOf ngMock.httpBackend
   * @description
   * Creates a new request expectation for PUT requests. For more info see `expect()`.
   *
   * @param {string|RegExp} url HTTP url.
   * @param {(string|RegExp)=} data HTTP request body.
   * @param {Object=} headers HTTP headers.
   * @returns {requestHandler} Returns an object with `respond` method that control how a matched
   *   request is handled.
   */
  _Chain expectPUT(url, [data, headers, withCredentials = false]) => expect('PUT', url, data,
      headers, withCredentials);

  /**
   * @ngdoc method
   * @name ngMock.httpBackend#expectPOST
   * @methodOf ngMock.httpBackend
   * @description
   * Creates a new request expectation for POST requests. For more info see `expect()`.
   *
   * @param {string|RegExp} url HTTP url.
   * @param {(string|RegExp)=} data HTTP request body.
   * @param {Object=} headers HTTP headers.
   * @returns {requestHandler} Returns an object with `respond` method that control how a matched
   *   request is handled.
   */
  _Chain expectPOST(url, [data, headers, withCredentials = false]) => expect('POST', url, data,
      headers, withCredentials);

  /**
   * @ngdoc method
   * @name ngMock.httpBackend#expectPATCH
   * @methodOf ngMock.httpBackend
   * @description
   * Creates a new request expectation for PATCH requests. For more info see `expect()`.
   *
   * @param {string|RegExp} url HTTP url.
   * @param {(string|RegExp)=} data HTTP request body.
   * @param {Object=} headers HTTP headers.
   * @returns {requestHandler} Returns an object with `respond` method that control how a matched
   *   request is handled.
   */
  _Chain expectPATCH(url, [data, headers, withCredentials = false]) => expect('PATCH', url, data,
      headers, withCredentials);

  /**
   * @ngdoc method
   * @name ngMock.httpBackend#expectHEAD
   * @methodOf ngMock.httpBackend
   * @description
   * Creates a new request expectation for HEAD requests. For more info see `expect()`.
   *
   * @param {string|RegExp} url HTTP url.
   * @param {Object=} headers HTTP headers.
   * @returns {requestHandler} Returns an object with `respond` method that control how a matched
   *   request is handled.
   */

  /**
   * @ngdoc method
   * @name ngMock.httpBackend#flush
   * @methodOf ngMock.httpBackend
   * @description
   * Flushes all pending requests using the trained responses.
   *
   * @param {number=} count Number of responses to flush (in the order they arrived). If undefined,
   *   all pending requests will be flushed. If there are no pending requests when the flush method
   *   is called an exception is thrown (as this typically a sign of programming error).
   */
  void flush([count]) {
    if (responses.isEmpty) throw ['No pending request to flush !'];

    if (count != null) {
      while (count-- > 0) {
        if (responses.isEmpty) throw ['No more pending request to flush !'];
        responses.removeAt(0)();
      }
    } else {
      while (!responses.isEmpty) {
        responses.removeAt(0)();
      }
    }
    verifyNoOutstandingExpectation();
  }


  /**
   * @ngdoc method
   * @name ngMock.httpBackend#verifyNoOutstandingExpectation
   * @methodOf ngMock.httpBackend
   * @description
   * Verifies that all of the requests defined via the `expect` api were made. If any of the
   * requests were not made, verifyNoOutstandingExpectation throws an exception.
   *
   * Typically, you would call this method following each test case that asserts requests using an
   * "afterEach" clause.
   *
   * <pre>
   *   afterEach(httpBackend.verifyNoOutstandingExpectation);
   * </pre>
   */
  void verifyNoOutstandingExpectation() {
    if (!expectations.isEmpty) {
      throw ['Unsatisfied requests: ${expectations.join(', ')}'];
    }
  }


  /**
   * @ngdoc method
   * @name ngMock.httpBackend#verifyNoOutstandingRequest
   * @methodOf ngMock.httpBackend
   * @description
   * Verifies that there are no outstanding requests that need to be flushed.
   *
   * Typically, you would call this method following each test case that asserts requests using an
   * "afterEach" clause.
   *
   * <pre>
   *   afterEach(httpBackend.verifyNoOutstandingRequest);
   * </pre>
   */
  void verifyNoOutstandingRequest() {
    if (!responses.isEmpty) throw ['Unflushed requests: ${responses.length}'];
  }


  /**
   * @ngdoc method
   * @name ngMock.httpBackend#resetExpectations
   * @methodOf ngMock.httpBackend
   * @description
   * Resets all request expectations, but preserves all backend definitions. Typically, you would
   * call resetExpectations during a multiple-phase test when you want to reuse the same instance of
   * httpBackend mock.
   */
  void resetExpectations() {
    expectations.length = 0;
    responses.length = 0;
  }
}

/**
 * Mock implementation of the [HttpRequest] object returned from the HttpBackend.
 */
class MockHttpRequest implements HttpRequest {
  final bool supportsCrossOrigin = false;
  final bool supportsLoadEndEvent = false;
  final bool supportsOverrideMimeType = false;
  final bool supportsProgressEvent = false;
  final Events on = null;

  final dart_async.Stream<ProgressEvent> onAbort = null;
  final dart_async.Stream<ProgressEvent> onError = null;
  final dart_async.Stream<ProgressEvent> onLoad = null;
  final dart_async.Stream<ProgressEvent> onLoadEnd = null;
  final dart_async.Stream<ProgressEvent> onLoadStart = null;
  final dart_async.Stream<ProgressEvent> onProgress = null;
  final dart_async.Stream<ProgressEvent> onReadyStateChange = null;

  final dart_async.Stream<ProgressEvent> onTimeout = null;
  final int readyState = 0;

  get responseText => response == null ? null : "$response";
  Map<String, String> get responseHeaders => null;
  final responseXml = null;
  final String statusText = null;
  final HttpRequestUpload upload = null;

  String responseType = null;
  int timeout = 0;
  bool withCredentials;

  final int status;
  final response;
  final String headers;

  MockHttpRequest(this.status, this.response, [this.headers]);

  void abort() {}
  bool dispatchEvent(Event event) => false;
  String getAllResponseHeaders() => headers;
  String getResponseHeader(String header) => null;

  void open(String method, String url, {bool async, String user, String password}) {}
  void overrideMimeType(String override) {}
  void send([data]) {}
  void setRequestHeader(String header, String value) {}
  void addEventListener(String type, EventListener listener, [bool useCapture]) {}
  void removeEventListener(String type, EventListener listener, [bool useCapture]) {}
}

class MockProgressEvent implements ProgressEvent {
  final bool bubbles = false;
  final bool cancelable = false;
  final DataTransfer clipboardData = null;
  final EventTarget currentTarget;
  final Element matchingTarget = null;
  final bool defaultPrevented = false;
  final int eventPhase = 0;
  final bool lengthComputable = false;
  final int loaded = 0;
  final List<Node> path = null;
  final int position = 0;
  final Type runtimeType = null;
  final EventTarget target = null;
  final int timeStamp = 0;
  final int total = 0;
  final int totalSize = 0;
  final String type = null;

  bool cancelBubble = false;

  MockProgressEvent(MockHttpRequest this.currentTarget);

  void preventDefault() {}
  void stopImmediatePropagation() {}
  void stopPropagation() {}
}
