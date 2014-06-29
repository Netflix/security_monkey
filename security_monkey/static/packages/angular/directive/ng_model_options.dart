part of angular.directive;

@Decorator(
    selector: 'input[ng-model-options]',
    map: const {'ng-model-options': '=>options'})
class NgModelOptions {
  static const String _DEBOUNCE_DEFAULT_KEY = "default";
  static const String _DEBOUNCE_BLUR_KEY = "blur";
  static const String _DEBOUNCE_CHANGE_KEY = "change";
  static const String _DEBOUNCE_INPUT_KEY = "input";

  int _debounceDefaultValue = 0;
  int _debounceBlurValue;
  int _debounceChangeValue;
  int _debounceInputValue;

  async.Timer _blurTimer;
  async.Timer _changeTimer;
  async.Timer _inputTimer;

  NgModelOptions();

  void set options(options) {
    if (options["debounce"] is int){
      _debounceDefaultValue = options["debounce"];
    } else {
      Map debounceOptions = options["debounce"];
      if (debounceOptions.containsKey(_DEBOUNCE_DEFAULT_KEY)){
        _debounceDefaultValue = debounceOptions[_DEBOUNCE_DEFAULT_KEY];
      }
      _debounceBlurValue   = debounceOptions[_DEBOUNCE_BLUR_KEY];
      _debounceChangeValue = debounceOptions[_DEBOUNCE_CHANGE_KEY];
      _debounceInputValue  = debounceOptions[_DEBOUNCE_INPUT_KEY];
    }
  }

  void executeBlurFunc(func()) {
    var delay = _debounceBlurValue == null ? _debounceDefaultValue : _debounceBlurValue;
    _blurTimer = _runFuncDebounced(delay, func, _blurTimer);
  }

  void executeChangeFunc(func()) {
    var delay = _debounceChangeValue == null ? _debounceDefaultValue : _debounceChangeValue;
    _changeTimer = _runFuncDebounced(delay, func, _changeTimer);
  }

  void executeInputFunc(func()) {
    var delay = _debounceInputValue == null ? _debounceDefaultValue : _debounceInputValue;
    _inputTimer = _runFuncDebounced(delay, func, _inputTimer);
  }

  async.Timer _runFuncDebounced(int delay, func(), async.Timer timer){
    if (timer != null && timer.isActive) timer.cancel();

    if (delay == 0){
      func();
      return null;
    } else {
      return new async.Timer(new Duration(milliseconds: delay), func);
    }
  }
}
