import 'package:angular/angular.dart';
import 'package:angular_ui/angular_ui.dart';
import 'package:angular/application_factory.dart';
import 'package:logging/logging.dart';

// Controllers
import 'package:SecurityMonkey/controller/username_controller.dart' show UsernameController;

// Components
import 'package:SecurityMonkey/component/itemdetails/itemdetails_component.dart';
import 'package:SecurityMonkey/component/revision_table_component/revision_table_component.dart';
import 'package:SecurityMonkey/component/item_table_component/item_table_component.dart';
import 'package:SecurityMonkey/component/revision/revision_component.dart';
import 'package:SecurityMonkey/component/issue_table_component/issue_table_component.dart';
import 'package:SecurityMonkey/component/account_view_component/account_view_component.dart';
import 'package:SecurityMonkey/component/search_page_component/search_page_component.dart';
import 'package:SecurityMonkey/component/search_bar_component/search_bar_component.dart';
import 'package:SecurityMonkey/component/signout_component/signout_component.dart';
import 'package:SecurityMonkey/component/settings_component/settings_component.dart';

// Services
import 'package:SecurityMonkey/service/revisions_service.dart';
import 'package:SecurityMonkey/service/items_service.dart';
import 'package:SecurityMonkey/service/itemdetails_service.dart';
import 'package:SecurityMonkey/service/user_settings_service.dart';
import 'package:SecurityMonkey/service/justify_service.dart';
import 'package:SecurityMonkey/service/revision_comment_service.dart';
import 'package:SecurityMonkey/service/revision_service.dart';
import 'package:SecurityMonkey/service/item_comment_service.dart';
import 'package:SecurityMonkey/service/username_service.dart';
import 'package:SecurityMonkey/service/issues_service.dart';
import 'package:SecurityMonkey/service/account_service.dart';

// Routing
import 'package:SecurityMonkey/routing/securitymonkey_router.dart';


// Temporary, please follow https://github.com/angular/angular.dart/issues/476
//@MirrorsUsed(
//  targets: const ['revisions_controller'],
//  override: '*')
//import 'dart:mirrors';

class SecurityMonkeyModule extends Module {

  SecurityMonkeyModule() {
    // AngularUI
    install(new AngularUIModule());
    
    // Controllers
    bind(UsernameController);

    // Components
    bind(ItemDetailsComponent);
    bind(RevisionTableComponent);
    bind(ItemTableComponent);
    bind(RevisionComponent);
    bind(IssueTableComponent);
    bind(AccountViewComponent);
    bind(SearchPageComponent);
    bind(SearchBarComponent);
    bind(SignoutComponent);
    bind(SettingsComponent);

    // Services
    bind(RevisionsService);
    bind(ItemsService);
    bind(ItemDetailsService);
    bind(UserSettingsService);
    bind(JustifyService);
    bind(RevisionCommentService);
    bind(RevisionService);
    bind(ItemCommentService);
    bind(UsernameService);
    bind(IssuesService);
    bind(AccountService);

    // Routing
    bind(RouteInitializerFn, toValue: securityMonkeyRouteInitializer);
    factory(NgRoutingUsePushState,
        (_) => new NgRoutingUsePushState.value(false));
  }
}


main() {
  Logger.root..level = Level.FINEST
             ..onRecord.listen((LogRecord rec) {
               print('${rec.level.name}: ${rec.time}: ${rec.message}');
               });
  applicationFactory()
        .addModule(new SecurityMonkeyModule())
        .run();
}