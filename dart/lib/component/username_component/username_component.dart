part of security_monkey;

@Component(
    selector: 'username',
    templateUrl: 'packages/security_monkey/component/username_component/username_component.html',
    useShadowDom: false)
class UsernameComponent {
    UsernameService us;
    UsernameComponent(this.us);

    get name => this.us.name;
    get signed_in => this.us.signed_in;

}
