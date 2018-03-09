library security_monkey_main;

import 'package:angular/application_factory.dart';
import 'package:logging/logging.dart';
import 'package:security_monkey/security_monkey.dart';

main() {
  Logger.root..level = Level.FINEST
             ..onRecord.listen((LogRecord rec) {
               print('${rec.level.name}: ${rec.time}: ${rec.message}');
               });
  final inj = applicationFactory()
        .addModule(new SecurityMonkeyModule())
        .run();
  GlobalHttpInterceptors.setUp(inj);
}