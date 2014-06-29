/**
 * All of the core directives available in Angular. This library is included as part of [angular
 * .dart](#angular/angular).
 *
 * A directive attaches a specified behavior to a DOM element. You can extend Angular by writing
 * your own directives and providing them as part of a custom library.
 *
 * Directives consist of a class specifying the behavior, and a directive annotation (such as a
 * [Decorator](#angular-core-annotation.Decorator) or a
 * [Component](#angular-core-annotation.Component)) that describes when the behavior should be
 * applied.
 *
 * For example:
 *
 *     <span ng-show="ctrl.isVisible">this text is conditionally visible</span>
 */
library angular.directive;

import 'package:di/di.dart';
import 'dart:html' as dom;
import 'dart:async' as async;
import 'package:intl/intl.dart';
import 'package:angular/core/annotation.dart';
import 'package:angular/core/module_internal.dart';
import 'package:angular/core/parser/parser.dart';
import 'package:angular/core_dom/module_internal.dart';
import 'package:angular/utils.dart';
import 'package:angular/change_detection/watch_group.dart';
import 'package:angular/change_detection/change_detection.dart';

part 'a_href.dart';
part 'ng_base_css.dart';
part 'ng_bind.dart';
part 'ng_bind_html.dart';
part 'ng_bind_template.dart';
part 'ng_class.dart';
part 'ng_events.dart';
part 'ng_cloak.dart';
part 'ng_if.dart';
part 'ng_include.dart';
part 'ng_control.dart';
part 'ng_model.dart';
part 'ng_pluralize.dart';
part 'ng_repeat.dart';
part 'ng_template.dart';
part 'ng_show_hide.dart';
part 'ng_src_boolean.dart';
part 'ng_style.dart';
part 'ng_switch.dart';
part 'ng_non_bindable.dart';
part 'ng_model_select.dart';
part 'ng_form.dart';
part 'ng_model_validators.dart';
part 'ng_model_options.dart';

/**
 * This module registers all the Angular directives.
 *
 * When instantiating an Angular application through applicationFactory,
 * DirectiveModule is automatically included.
 */
class DirectiveModule extends Module {
  DirectiveModule() {
    bind(AHref, toValue: null);
    bind(NgBaseCss);  // The root injector should have an empty NgBaseCss
    bind(NgBind, toValue: null);
    bind(NgBindTemplate, toValue: null);
    bind(NgBindHtml, toValue: null);
    bind(dom.NodeValidator, toFactory: (_) => new dom.NodeValidatorBuilder.common());
    bind(NgClass, toValue: null);
    bind(NgClassOdd, toValue: null);
    bind(NgClassEven, toValue: null);
    bind(NgCloak, toValue: null);
    bind(NgHide, toValue: null);
    bind(NgIf, toValue: null);
    bind(NgUnless, toValue: null);
    bind(NgInclude, toValue: null);
    bind(NgPluralize, toValue: null);
    bind(NgRepeat, toValue: null);
    bind(NgShow, toValue: null);
    bind(InputTextLike, toValue: null);
    bind(InputDateLike, toValue: null);
    bind(InputNumberLike, toValue: null);
    bind(InputRadio, toValue: null);
    bind(InputCheckbox, toValue: null);
    bind(InputSelect, toValue: null);
    bind(OptionValue, toValue: null);
    bind(ContentEditable, toValue: null);
    bind(NgBindTypeForDateLike, toValue: null);
    bind(NgModel, toValue: null);
    bind(NgModelOptions, toValue: new NgModelOptions());
    bind(NgValue, toValue: null);
    bind(NgTrueValue, toValue: new NgTrueValue());
    bind(NgFalseValue, toValue: new NgFalseValue());
    bind(NgSwitch, toValue: null);
    bind(NgSwitchWhen, toValue: null);
    bind(NgSwitchDefault, toValue: null);

    bind(NgBooleanAttribute, toValue: null);
    bind(NgSource, toValue: null);
    bind(NgAttribute, toValue: null);

    bind(NgEvent, toValue: null);
    bind(NgStyle, toValue: null);
    bind(NgNonBindable, toValue: null);
    bind(NgTemplate, toValue: null);
    bind(NgControl, toValue: new NgNullControl());
    bind(NgForm, toValue: new NgNullForm());

    bind(NgModelRequiredValidator, toValue: null);
    bind(NgModelUrlValidator, toValue: null);
    bind(NgModelEmailValidator, toValue: null);
    bind(NgModelNumberValidator, toValue: null);
    bind(NgModelMaxNumberValidator, toValue: null);
    bind(NgModelMinNumberValidator, toValue: null);
    bind(NgModelPatternValidator, toValue: null);
    bind(NgModelMinLengthValidator, toValue: null);
    bind(NgModelMaxLengthValidator, toValue: null);
  }
}
