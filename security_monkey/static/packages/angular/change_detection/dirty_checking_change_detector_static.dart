library dirty_checking_change_detector_static;

import 'package:angular/change_detection/change_detection.dart';

class StaticFieldGetterFactory implements FieldGetterFactory {
  Map<String, FieldGetter> getters;

  StaticFieldGetterFactory(this.getters);

  FieldGetter getter(Object object, String name) {
    var getter = getters[name];
    if (getter == null) throw "Missing getter: (o) => o.$name";
    return getter;
  }
}
