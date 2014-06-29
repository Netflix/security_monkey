part of angular.mock;

/**
 * Mock implementation of [ExceptionHandler] that rethrows exceptions.
 */
class RethrowExceptionHandler extends ExceptionHandler {
  call(error, stack, [reason]){
    throw "$error $reason \nORIGINAL STACKTRACE:\n $stack";
  }
}

class ExceptionWithStack {
  final dynamic error;
  final dynamic stack;
  ExceptionWithStack(this.error, this.stack);
  toString() => "$error\n$stack";
}

/**
 * Mock implementation of [ExceptionHandler] that logs all exceptions for
 * later processing.
 */
class LoggingExceptionHandler implements ExceptionHandler {
  /**
   * All exceptions are stored here for later examining.
   */
  final errors = <ExceptionWithStack>[];

  call(error, stack, [reason]) {
    errors.add(new ExceptionWithStack(error, stack));
  }

  /**
   * This method throws an exception if the errors is not empty.
   * It is recommended that this method is called on test tear-down
   * to verify that all exceptions have been processed.
   */
  assertEmpty() {
    if (errors.isNotEmpty) {
      throw new ArgumentError('Exception Logger not empty:\n$errors');
    }
  }
}
