part of angular.directive;

/**
 * NgValidator is the class interface for performing validations for an NgModel instance.
 */
abstract class NgValidator {
  /**
   * The name of the validator. This name will be used as the key value within the
   * model.errorStates map and it will also be applied as a CSS class on the associated
   * DOM element. Therefore, as a best practice, please do not include spaces for the validator
   * name since it may cause issues with the CSS naming.
   */
  String get name;
  bool isValid(modelValue);
}

/**
 * Validates the model depending if required or ng-required is present on the element.
 */
@Decorator(
    selector: '[ng-model][required]')
@Decorator(
    selector: '[ng-model][ng-required]',
    map: const {'ng-required': '=>required'})
class NgModelRequiredValidator implements NgValidator {

  final String name = 'ng-required';
  bool _required = true;
  final NgModel _ngModel;

  NgModelRequiredValidator(NgModel this._ngModel) {
    _ngModel.addValidator(this);
  }

  bool isValid(modelValue) {
    // Any element which isn't required is always valid.
    if (!_required) return true;
    // Null is not a value, therefore not valid.
    if (modelValue == null) return false;
    // Empty lists and/or strings are not valid.
    // NOTE: This is an excellent use case for structural typing.
    //   We really want anything object that has a 'isEmpty' property.
    return !((modelValue is List || modelValue is String) && modelValue.isEmpty);
  }

  set required(value) {
    _required = value == null ? false : value;
    _ngModel.validateLater();
  }
}

/**
 * Validates the model to see if its contents match a valid URL pattern.
 */
@Decorator(selector: 'input[type=url][ng-model]')
class NgModelUrlValidator implements NgValidator {
  static final URL_REGEXP = new RegExp(
      r'^(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?' +
      r'(\/|\/([\w#!:.?+=&%@!\-\/]))?$');

  final String name = 'ng-url';

  NgModelUrlValidator(NgModel ngModel) {
    ngModel.addValidator(this);
  }

  bool isValid(modelValue) =>
      modelValue == null || modelValue.isEmpty || URL_REGEXP.hasMatch(modelValue);
}

/**
 * Validates the model to see if its contents match a valid email pattern.
 */
@Decorator(selector: 'input[type=email][ng-model]')
class NgModelEmailValidator implements NgValidator {
  static final EMAIL_REGEXP = new RegExp(
      r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,6}$');

  final String name = 'ng-email';

  NgModelEmailValidator(NgModel ngModel) {
    ngModel.addValidator(this);
  }

  bool isValid(modelValue) =>
      modelValue == null || modelValue.isEmpty || EMAIL_REGEXP.hasMatch(modelValue);
}

/**
 * Validates the model to see if its contents match a valid number.
 */
@Decorator(selector: 'input[type=number][ng-model]')
@Decorator(selector: 'input[type=range][ng-model]')
class NgModelNumberValidator implements NgValidator {

  final String name = 'ng-number';

  NgModelNumberValidator(NgModel ngModel) {
    ngModel.addValidator(this);
  }

  bool isValid(modelValue) {
    if (modelValue != null) {
      try {
        num val = double.parse(modelValue.toString());
        if (val.isNaN) {
          return false;
        }
      } catch(exception, stackTrace) {
        return false;
      }
    }
    return true;
  }
}

/**
 * Validates the model to see if the numeric value than or equal to the max value.
 */
@Decorator(selector: 'input[type=number][ng-model][max]')
@Decorator(selector: 'input[type=range][ng-model][max]')
@Decorator(
    selector: 'input[type=number][ng-model][ng-max]',
    map: const {'ng-max': '=>max'})
@Decorator(
    selector: 'input[type=range][ng-model][ng-max]',
    map: const {'ng-max': '=>max'})
class NgModelMaxNumberValidator implements NgValidator {

  final String name = 'ng-max';
  double _max;
  final NgModel _ngModel;

  NgModelMaxNumberValidator(NgModel this._ngModel) {
    _ngModel.addValidator(this);
  }

  @NgAttr('max')
  get max => _max;
  set max(value) {
    try {
      num parsedValue = double.parse(value);
      _max = parsedValue.isNaN ? _max : parsedValue;
    } catch(e) {
      _max = null;
    } finally {
      _ngModel.validateLater();
    }
  }

  bool isValid(modelValue) {
    if (modelValue == null || max == null) return true;

    try {
      num parsedValue = double.parse(modelValue.toString());
      if (!parsedValue.isNaN) {
        return parsedValue <= max;
      }
    } catch(exception, stackTrace) {}

    //this validator doesn't care if the type conversation fails or the value
    //is not a number (NaN) because NgModelNumberValidator will handle the
    //number-based validation either way.
    return true;
  }
}

/**
 * Validates the model to see if the numeric value is greater than or equal to the min value.
 */
@Decorator(selector: 'input[type=number][ng-model][min]')
@Decorator(selector: 'input[type=range][ng-model][min]')
@Decorator(
    selector: 'input[type=number][ng-model][ng-min]',
    map: const {'ng-min': '=>min'})
@Decorator(
    selector: 'input[type=range][ng-model][ng-min]',
    map: const {'ng-min': '=>min'})
class NgModelMinNumberValidator implements NgValidator {

  final String name = 'ng-min';
  double _min;
  final NgModel _ngModel;

  NgModelMinNumberValidator(NgModel this._ngModel) {
    _ngModel.addValidator(this);
  }

  @NgAttr('min')
  get min => _min;
  set min(value) {
    try {
      num parsedValue = double.parse(value);
      _min = parsedValue.isNaN ? _min : parsedValue;
    } catch(e) {
      _min = null;
    } finally {
      _ngModel.validateLater();
    }
  }

  bool isValid(modelValue) {
    if (modelValue == null || min == null) return true;

    try {
      num parsedValue = double.parse(modelValue.toString());
      if (!parsedValue.isNaN) {
        return parsedValue >= min;
      }
    } catch(exception, stackTrace) {}

    //this validator doesn't care if the type conversation fails or the value
    //is not a number (NaN) because NgModelNumberValidator will handle the
    //number-based validation either way.
    return true;
  }
}

/**
 * Validates the model to see if its contents match the given pattern present on either the
 * HTML pattern or ng-pattern attributes present on the input element.
 */
@Decorator(selector: '[ng-model][pattern]')
@Decorator(
    selector: '[ng-model][ng-pattern]',
    map: const {'ng-pattern': '=>pattern'})
class NgModelPatternValidator implements NgValidator {

  final String name = 'ng-pattern';
  RegExp _pattern;
  final NgModel _ngModel;

  NgModelPatternValidator(NgModel this._ngModel) {
    _ngModel.addValidator(this);
  }

  bool isValid(modelValue) {
    //remember, only required validates for the input being empty
    return _pattern == null || modelValue == null || modelValue.length == 0 ||
           _pattern.hasMatch(modelValue);
  }

  @NgAttr('pattern')
  void set pattern(val) {
    _pattern = val != null && val.length > 0 ? new RegExp(val) : null;
    _ngModel.validateLater();
  }
}

/**
 * Validates the model to see if the length of its contents are greater than or
 * equal to the minimum length set in place by the HTML minlength or
 * ng-minlength attributes present on the input element.
 */
@Decorator(selector: '[ng-model][minlength]')
@Decorator(
    selector: '[ng-model][ng-minlength]',
    map: const {'ng-minlength': '=>minlength'})
class NgModelMinLengthValidator implements NgValidator {

  final String name = 'ng-minlength';
  int _minlength;
  final NgModel _ngModel;

  NgModelMinLengthValidator(NgModel this._ngModel) {
    _ngModel.addValidator(this);
  }

  bool isValid(modelValue) {
    //remember, only required validates for the input being empty
    return _minlength == 0 || modelValue == null || modelValue.length == 0 ||
           modelValue.length >= _minlength;
  }

  @NgAttr('minlength')
  void set minlength(value) {
    _minlength = value == null ? 0 : int.parse(value.toString());
    _ngModel.validateLater();
  }
}

/**
 * Validates the model to see if the length of its contents are less than or
 * equal to the maximum length set in place by the HTML maxlength or
 * ng-maxlength attributes present on the input element.
 */
@Decorator(selector: '[ng-model][maxlength]')
@Decorator(
    selector: '[ng-model][ng-maxlength]',
    map: const {'ng-maxlength': '=>maxlength'})
class NgModelMaxLengthValidator implements NgValidator {

  final String name = 'ng-maxlength';
  int _maxlength = 0;
  final NgModel _ngModel;

  NgModelMaxLengthValidator(NgModel this._ngModel) {
    _ngModel.addValidator(this);
  }

  bool isValid(modelValue) =>
      _maxlength == 0 || (modelValue == null ? 0 : modelValue.length) <= _maxlength;

  @NgAttr('maxlength')
  void set maxlength(value) {
    _maxlength = value == null ? 0 : int.parse(value.toString());
    _ngModel.validateLater();
  }
}
