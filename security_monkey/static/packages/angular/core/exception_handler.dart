part of angular.core_internal;

/**
 * Any uncaught exception in angular expressions is delegated to this service.
 * The default implementation logs exceptions into console.
 *
 * In your application it is expected that this service is overridden with
 * your implementation which can store the exception for later processing.
 */
@Injectable()
class ExceptionHandler {

 /**
  * Delegate uncaught exception for central error handling.
  *
  * - [error] The error which was caught.
  * - [stack] The stacktrace.
  * - [reason] Optional contextual information for the error.
  */
  call(dynamic error, dynamic stack, [String reason = '']) {
    print("$error\n$reason\nSTACKTRACE:\n$stack");
  }
}
