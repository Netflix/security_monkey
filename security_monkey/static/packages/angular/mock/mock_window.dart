part of angular.mock;

@proxy
class MockWindow extends Mock implements Window {
  final history = new MockHistory();
  final location = new MockLocation();
  final document = new MockDocument();

  final onPopStateController = new dart_async.StreamController<PopStateEvent>();
  final onHashChangeController = new dart_async.StreamController<Event>();
  final onClickController = new dart_async.StreamController<MouseEvent>();

  dart_async.Stream<PopStateEvent> get onPopState => onPopStateController.stream;
  dart_async.Stream<Event> get onHashChange => onHashChangeController.stream;
  dart_async.Stream<Event> get onClick => onClickController.stream;
  dart_async.Future<num> get animationFrame => animationFrameCompleter.future;
  
  executeAnimationFrame([num time=0.0]) {
    var last = animationFrameCompleter;
    animationFrameCompleter = new dart_async.Completer<num>();
    last.complete(time);
  }
      
  noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

@proxy
class MockHistory extends Mock implements History {
  noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

@proxy
class MockLocation extends Mock implements Location {
  noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

@proxy
class MockDocument extends Mock implements HtmlDocument {
  noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}
