part of angular.directive;

/**
 * Contains info and error states used during form and input validation.
 *
 * NgControl is a common superclass for forms and input controls that handles info and error states, as well as
 * status flags. NgControl is used with the form and fieldset as well as all other directives that are used for
 * user input with NgModel.
 */
abstract class NgControl implements AttachAware, DetachAware {
  static const NG_VALID          = "ng-valid";
  static const NG_INVALID        = "ng-invalid";
  static const NG_PRISTINE       = "ng-pristine";
  static const NG_DIRTY          = "ng-dirty";
  static const NG_TOUCHED        = "ng-touched";
  static const NG_UNTOUCHED      = "ng-untouched";
  static const NG_SUBMIT_VALID   = "ng-submit-valid";
  static const NG_SUBMIT_INVALID = "ng-submit-invalid";

  String _name;
  bool _submitValid;

  final NgControl _parentControl;
  final Animate _animate;
  final NgElement _element;

  final _controls = new List<NgControl>();
  final _controlByName = new Map<String, List<NgControl>>();

  /**
    * The list of errors present on the control represented by an error name and
    * an inner control instance.
    */
  final errorStates = new Map<String, Set<NgControl>>();

  /**
    * The list of info messages present on the control represented by an state name and
    * an inner control instance.
    */
  final infoStates = new Map<String, Set<NgControl>>();

  NgControl(NgElement this._element, Injector injector,
      Animate this._animate)
      : _parentControl = injector.parent.get(NgControl);

  @override
  void attach() {
    _parentControl.addControl(this);
  }

  @override
  void detach() {
    _parentControl..removeStates(this)..removeControl(this);
  }

  /**
    * Resets the form and inner models to their pristine state.
    */
  void reset() {
    _controls.forEach((control) {
      control.reset();
    });
  }

  void onSubmit(bool valid) {
    if (valid) {
      _submitValid = true;
      element..addClass(NG_SUBMIT_VALID)..removeClass(NG_SUBMIT_INVALID);
    } else {
      _submitValid = false;
      element..addClass(NG_SUBMIT_INVALID)..removeClass(NG_SUBMIT_VALID);
    }
    _controls.forEach((control) {
      control.onSubmit(valid);
    });
  }

  NgControl get parentControl => _parentControl;

  /**
    * Whether or not the form has been submitted yet.
    */
  bool get submitted => _submitValid != null;

  /**
    * Whether or not the form was valid when last submitted.
    */
  bool get validSubmit => _submitValid == true;

  /**
    * Whether or not the form was invalid when last submitted.
    */
  bool get invalidSubmit => _submitValid == false;

  String get name => _name;
  void set name(String value) {
    _name = value;
  }

  /**
    * Whether or not the form was invalid when last submitted.
    */
  NgElement get element => _element;

  /**
    * A control is considered valid if all inner models are valid.
    */
  bool get valid              => !invalid;

  /**
    * A control is considered invalid if any inner models are invalid.
    */
  bool get invalid            => errorStates.isNotEmpty;

  /**
    * Whether or not the control's or model's data has not been changed.
    */
  bool get pristine           => !dirty;

  /**
    * Whether or not the control's or model's data has been changed.
    */
  bool get dirty              => infoStates.containsKey(NG_DIRTY);

  /**
    * Whether or not the control/model has not been interacted with by the user.
    */
  bool get untouched          => !touched;

  /**
    * Whether or not the control/model has been interacted with by the user.
    */
  bool get touched            => infoStates.containsKey(NG_TOUCHED);

  /**
   * Registers a form control into the form for validation.
   *
   * * [control] - The form control which will be registered (see [NgControl]).
   */
  void addControl(NgControl control) {
    _controls.add(control);
    if (control.name != null) {
      _controlByName.putIfAbsent(control.name, () => <NgControl>[]).add(control);
    }
  }

  /**
   * De-registers a form control from the list of controls associated with the
   * form.
   *
   * * [control] - The form control which will be de-registered (see [NgControl]).
   */
  void removeControl(NgControl control) {
    _controls.remove(control);
    String key = control.name;
    if (key != null && _controlByName.containsKey(key)) {
      _controlByName[key].remove(control);
      if (_controlByName[key].isEmpty) _controlByName.remove(key);
    }
  }

  /**
   * Clears all the info and error states that are associated with the control.
   *
   * * [control] - The form control which will be cleared of all state (see [NgControl]).
   */
  void removeStates(NgControl control) {
    bool hasRemovals = false;
    errorStates.keys.toList().forEach((state) {
      Set matchingControls = errorStates[state];
      matchingControls.remove(control);
      if (matchingControls.isEmpty) {
        errorStates.remove(state);
        hasRemovals = true;
      }
    });

    infoStates.keys.toList().forEach((state) {
      Set matchingControls = infoStates[state];
      matchingControls.remove(control);
      if (matchingControls.isEmpty) {
        infoStates.remove(state);
        hasRemovals = true;
      }
    });

    if (hasRemovals) _parentControl.removeStates(this);
  }

  /**
   * Whether or not the control contains the given error.
   *
   * * [errorName] - The name of the error (e.g. ng-required, ng-pattern, etc...)
   */
  bool hasErrorState(String errorName) => errorStates.containsKey(errorName);

  /**
   * Adds the given childControl/errorName to the list of errors present on the control. Once
   * added all associated parent controls will be registered with the error as well.
   *
   * * [childControl] - The child control that contains the error.
   * * [errorName] - The name of the given error (e.g. ng-required, ng-pattern, etc...).
   */
  void addErrorState(NgControl childControl, String errorName) {
    element..addClass(errorName + '-invalid')..removeClass(errorName + '-valid');
    errorStates.putIfAbsent(errorName, () => new Set()).add(childControl);
    _parentControl.addErrorState(this, errorName);
  }

  /**
   * Removes the given childControl/errorName from the list of errors present on the control. Once
   * removed the control will update any parent controls depending if error is not present on
   * any other inner controls and or models.
   *
   * * [childControl] - The child control that contains the error.
   * * [errorName] - The name of the given error (e.g. ng-required, ng-pattern, etc...).
   */
  void removeErrorState(NgControl childControl, String errorName) {
    if (!errorStates.containsKey(errorName)) return;

    bool hasError = _controls.any((child) => child.hasErrorState(errorName));
    if (!hasError) {
      errorStates.remove(errorName);
      _parentControl.removeErrorState(this, errorName);
      element..removeClass(errorName + '-invalid')..addClass(errorName + '-valid');
    }
  }

  String _getOppositeInfoState(String state) {
    switch(state) {
      case NG_DIRTY:
        return NG_PRISTINE;
      case NG_TOUCHED:
        return NG_UNTOUCHED;
      default:
        //not all info states have an opposite value
        return null;
    }
  }

  /**
   * Registers a non-error state on the control with the given childControl/stateName data. Once
   * added the control will also add the same data to any associated parent controls.
   *
   * * [childControl] - The child control that contains the error.
   * * [stateName] - The name of the given error (e.g. ng-required, ng-pattern, etc...).
   */
  void addInfoState(NgControl childControl, String stateName) {
    String oppositeState = _getOppositeInfoState(stateName);
    if (oppositeState != null) element.removeClass(oppositeState);
    element.addClass(stateName);
    infoStates.putIfAbsent(stateName, () => new Set()).add(childControl);
    _parentControl.addInfoState(this, stateName);
  }

  /**
   * De-registers the provided state on the control with the given childControl. The state
   * will be fully removed from the control if all of the inner controls/models also do not
   * contain the state. If so then the state will also be attempted to be removed from the
   * associated parent controls.
   *
   * * [childControl] - The child control that contains the error.
   * * [stateName] - The name of the given error (e.g. ng-required, ng-pattern, etc...).
   */
  void removeInfoState(NgControl childControl, String stateName) {
    String oppositeState = _getOppositeInfoState(stateName);
    if (infoStates.containsKey(stateName)) {
      bool hasState = _controls.any((child) =>
          child.infoStates.containsKey(stateName));
      if (!hasState) {
        if (oppositeState != null) element.addClass(oppositeState);
        element.removeClass(stateName);
        infoStates.remove(stateName);
        _parentControl.removeInfoState(this, stateName);
      }
    } else if (oppositeState != null) {
      NgControl parent = this;
      do {
        parent.element..addClass(oppositeState)..removeClass(stateName);
        parent = parent.parentControl;
      }
      while(parent != null && parent is! NgNullControl);
    }
  }
}

class NgNullControl implements NgControl {
  var _name, _dirty, _valid, _submitValid, _pristine, _element, _touched;
  var _controls, _parentControl, _controlName, _animate, infoStates, errorStates;
  var errors, _controlByName;
  NgElement element;

  void onSubmit(bool valid) {}

  void addControl(control) {}
  void removeControl(control) {}
  void updateControlValidity(NgControl ctrl, String errorType, bool isValid) {}

  String get name => null;
  void set name(name) {}

  bool get submitted => false;
  bool get validSubmit => true;
  bool get invalidSubmit => false;
  bool get pristine => true;
  bool get dirty => false;
  bool get valid => true;
  bool get invalid => false;
  bool get touched => false;
  bool get untouched => true;

  get parentControl => null;

  String _getOppositeInfoState(String state) => null;
  void addErrorState(NgControl control, String state) {}
  void removeErrorState(NgControl control, String state) {}
  void addInfoState(NgControl control, String state) {}
  void removeInfoState(NgControl control, String state) {}

  void reset() {}
  void attach() {}
  void detach() {}

  bool hasErrorState(String key) => false;

  void removeStates(NgControl control) {}
}
