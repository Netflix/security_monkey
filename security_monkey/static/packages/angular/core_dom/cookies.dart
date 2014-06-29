part of angular.core.dom_internal;

/**
* This class provides low-level acces to the browser's cookies.
* It is not meant to be used directly by applications.  Instead
* use the Cookies service.
*
*/
@Injectable()
class BrowserCookies {
  ExceptionHandler _exceptionHandler;
  dom.Document _document;

  var lastCookies = {};
  var lastCookieString = '';
  var cookiePath;
  var baseElement;

  BrowserCookies(this._exceptionHandler) {
    // Injecting document produces the error 'Caught Compile-time error during mirrored execution:
    // <'file:///mnt/data/b/build/slave/dartium-lucid32-full-trunk/build/src/out/Release/gen/blink/
    // bindings/dart/dart/html/Document.dart': Error: line 7 pos 3: expression must be a compile-time constant
    // @ DocsEditable '
    // I have not had time to debug it yet.
    _document = dom.document;

    var baseElementList = _document.getElementsByName('base');
    if (baseElementList.isEmpty) return;
    baseElement = baseElementList.first;
    cookiePath = _baseHref();
  }

  var URL_PROTOCOL = new RegExp(r'^https?\:\/\/[^\/]*');
  _baseHref() {
    var href = baseElement != null ? baseElement.attr('href') : null;
    return href != null ? href.replace(URL_PROTOCOL, '') : '';
  }

  // NOTE(deboer): This is sub-optimal, see dartbug.com/14281
  _unescape(s) => Uri.decodeFull(s);
  _escape(s) =>
    Uri.encodeFull(s)
      .replaceAll('=', '%3D')
      .replaceAll(';', '%3B');

  _updateLastCookies() {
    if (_document.cookie != lastCookieString) {
      lastCookieString = _document.cookie;
      List<String> cookieArray = lastCookieString.split("; ");
      lastCookies = {};

      // The first value that is seen for a cookie is the most specific one.
      // Values for the same cookie name that follow are for less specific paths.
      // Hence we reverse the array.
      cookieArray.reversed.forEach((cookie) {
        var index = cookie.indexOf('=');
        if (index > 0) { //ignore nameless cookies
          var name = _unescape(cookie.substring(0, index));
          lastCookies[name] = _unescape(cookie.substring(index + 1));
        }
      });
    }
    return lastCookies;
  }

  /**
   * Returns a cookie.
   */
  operator[](key) => _updateLastCookies()[key];

  /**
   * Sets a cookie.  Setting a cookie to [null] deletes the cookie.
   */
  operator[]=(name, value) {
    if (identical(value, null)) {
      _document.cookie = "${_escape(name)}=;path=$cookiePath;expires=Thu, 01 Jan 1970 00:00:00 GMT";
    } else {
      if (value is String) {
        var cookieLength = (_document.cookie = "${_escape(name)}=${_escape(value)};path=$cookiePath").length + 1;

        // per http://www.ietf.org/rfc/rfc2109.txt browser must allow at minimum:
        // - 300 cookies
        // - 20 cookies per unique domain
        // - 4096 bytes per cookie
        if (cookieLength > 4096) {
          _exceptionHandler("Cookie '$name' possibly not set or overflowed because it was " +
                "too large ($cookieLength > 4096 bytes)!", null);
        }
      }
    }
  }

  get all => _updateLastCookies();
}

/**
 *   Cookies service
 */
@Injectable()
class Cookies {
  BrowserCookies _browserCookies;
  Cookies(this._browserCookies);

  /**
   * Returns the value of given cookie key
   */
  operator[](name) => this._browserCookies[name];

  /**
   * Sets a value for given cookie key
   */
  operator[]=(name, value) => this._browserCookies[name] = value;

  /**
   * Remove given cookie
   */
  remove(name) => this._browserCookies[name] = null;
}

