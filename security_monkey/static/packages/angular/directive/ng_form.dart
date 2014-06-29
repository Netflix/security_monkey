part of angular.directive;

/**
 * The form directive listens on submission requests and, depending,
 * on if an action is set, the form will automatically either allow
 * or prevent the default browser submission from occurring.
 */
@Decorator(
    selector: 'form',
    module: NgForm.module)
@Decorator(
    selector: 'fieldset',
    module: NgForm.module)
@Decorator(
    selector: '.ng-form',
    module: NgForm.module)
@Decorator(
    selector: '[ng-form]',
    module: NgForm.module,
    map: const { 'ng-form': '@name' })
class NgForm extends NgControl {
  static final Module _module = new Module()
      ..bind(NgControl, toFactory: (i) => i.get(NgForm));
  static module() => _module;

  final Scope _scope;

  /**
   * Instantiates a new instance of NgForm. Upon creation, the instance of the
   * class will be bound to the formName property on the scope (where formName
   * refers to the name value acquired from the name attribute present on the
   * form DOM element).
   *
   * * [scope] - The scope to bind the form instance to.
   * * [element] - The form DOM element.
   * * [injector] - An instance of Injector.
   */
  NgForm(this._scope, NgElement element, Injector injector, Animate animate) :
    super(element, injector, animate) {

    if (!element.node.attributes.containsKey('action')) {
      element.node.onSubmit.listen((event) {
        event.preventDefault();
        onSubmit(valid == true);
        if (valid == true) {
          reset();
        }
      });
    }
  }

  /**
    * The name of the control. This is usually fetched via the name attribute that is
    * present on the element that the control is bound to.
    */
  @NgAttr('name')
  get name => _name;
  set name(String value) {
    if (value != null) {
      super.name = value;
      _scope.context[name] = this;
    }
  }

  /**
    * The list of associated child controls.
    */
  get controls => _controlByName;

  /**
    * Returns the child control that is associated with the given name. If multiple
    * child controls contain the same name then the first instance will be returned.
    */
  NgControl operator[](String name) =>
      controls.containsKey(name) ? controls[name][0] : null;
}

class NgNullForm extends NgNullControl implements NgForm {
  var _scope;

  NgNullForm() {}
  operator []=(String key, value) {}
  operator[](name) {}

  get controls => null;
}
