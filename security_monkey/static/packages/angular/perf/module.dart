/**
*
* Classes and utilities for analyzing performance in AngularDart.
*
* This is an optional library. You must import it in addition to the [angular.dart]
* (#angular/angular) library,
* like so:
*
*      import 'package:angular/angular.dart';
*      import 'package:angular/perf/module.dart';
*
*
*/
library angular.perf;

import 'dart:html' as dom;

import 'package:di/di.dart';
import 'package:perf_api/perf_api.dart';

part 'dev_tools_timeline.dart';

class PerfModule extends Module {
  PerfModule() {
    bind(Profiler, toImplementation: Profiler);
  }
}
