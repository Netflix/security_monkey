part of angular.mock;

/**
 * A convenient way to assert the order in which the DOM elements are processed.
 *
 * In your test create:
 *
 *     <div log="foo">...</div>
 *
 * And then assert:
 *
 *     expect(logger).toEqual(['foo']);
 */
@Decorator(
    selector: '[log]',
    map: const {
        'log': '@logMessage'
    })
class LogAttrDirective implements AttachAware {
  final Logger log;
  String logMessage;
  LogAttrDirective(this.log);
  void attach() {
    log(logMessage == '' ? 'LOG' : logMessage);
  }
}

/**
 * A convenient way to verify that a set of operations executed in a specific
 * order. Simply inject the Logger into each operation and call:
 *
 *     operation1(Logger logger) => logger('foo');
 *     operation2(Logger logger) => logger('bar');
 *
 *  Then in the test:
 *
 *     expect(logger).toEqual(['foo', 'bar']);
 */
class Logger extends ListBase {
  final tokens = [];

  /**
   * Add string token to the list.
   */
  void call(text) {
    tokens.add(text);
  }

  /**
   * Return a `;` separated list of recorded tokens.
   */
  String result() => tokens.join('; ');


  int get length => tokens.length;

  operator [](int index) => tokens[index];

  void operator []=(int index, value) {
    tokens[index] = value;
  }

  void set length(int newLength) {
    tokens.length = newLength;
  }
}
