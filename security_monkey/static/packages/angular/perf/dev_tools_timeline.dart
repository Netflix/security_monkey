part of angular.perf;

class DevToolsTimelineProfiler extends Profiler {
  final dom.Console console = dom.window.console;
  String prefix = '';

  String startTimer(String name, [dynamic extraData]) {
    console.time('$prefix$name');
    prefix = '$prefix  ';
    return name;
  }

  void stopTimer(dynamic name) {
    prefix = prefix.length > 0 ? prefix.substring(0, prefix.length - 2) : prefix;
    console.timeEnd('$prefix$name');
  }

  void markTime(String name, [dynamic extraData]) {
    console.timeStamp('$prefix$name');
  }
}
