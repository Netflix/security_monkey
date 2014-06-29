/**
 * All of the core formatters available in Angular. This library is included as part of
 * [angular.dart](#angular/angular).
 *
 * A formatter is a pure function that performs a transformation on input data from an expression.
 * You can extend Angular by writing your own formatters and providing them as part of a custom
 * library. See the @[Formatter](#angular-core-annotation.Formatter) class annotation for more
 * detail.
 *
 * Formatters are typically used within `{{ }}` to
 * convert data to human-readable form. They may also be used inside repeaters to transform arrays.
 *
 * For example:
 *
 *     {{ expression | uppercase }}
 *
 * or, in a repeater:
 *
 *      <div ng-repeat="item in items | limitTo:2">
 */
library angular.formatter;

export "package:angular/formatter/module_internal.dart" show
    FormatterModule,
    Currency,
    Date,
    Filter,
    Json,
    LimitTo,
    Lowercase,
    Arrayify,
    Number,
    OrderBy,
    Uppercase,
    Stringify;
