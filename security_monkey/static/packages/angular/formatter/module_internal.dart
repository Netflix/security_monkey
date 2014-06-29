library angular.formatter_internal;

import 'dart:convert' show JSON;
import 'package:intl/intl.dart';
import 'package:di/di.dart';
import 'package:angular/core/annotation.dart';
import 'package:angular/core/module_internal.dart';
import 'package:angular/core/parser/parser.dart';

part 'currency.dart';
part 'date.dart';
part 'filter.dart';
part 'json.dart';
part 'limit_to.dart';
part 'lowercase.dart';
part 'arrayify.dart';
part 'number.dart';
part 'order_by.dart';
part 'uppercase.dart';
part 'stringify.dart';

/**
 * This module registers all the Angular formatters.
 *
 * When instantiating an Angular application through
 * [applicationFactory](#angular-app-factory@id_applicationFactory), FormatterModule is
 * automatically included.
 */
class FormatterModule extends Module {
  FormatterModule() {
    bind(Arrayify);
    bind(Currency);
    bind(Date);
    bind(Filter);
    bind(Json);
    bind(LimitTo);
    bind(Lowercase);
    bind(Number);
    bind(OrderBy);
    bind(Uppercase);
    bind(Stringify);
  }
}
