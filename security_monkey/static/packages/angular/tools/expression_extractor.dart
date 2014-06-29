library angular.tools.html_expression_extractor;

import 'dart:async';
import 'dart:io';
import 'package:angular/tools/html_extractor.dart';
import 'package:angular/tools/source_metadata_extractor.dart';
import 'package:angular/tools/source_crawler_impl.dart';
import 'package:angular/tools/io.dart';
import 'package:angular/tools/io_impl.dart';
import 'package:angular/tools/common.dart';

import 'package:di/di.dart';
import 'package:di/dynamic_injector.dart';

import 'package:angular/core/parser/parser.dart';
import 'package:angular/tools/parser_getter_setter/generator.dart';

main(args) {
  if (args.length < 5) {
    print('Usage: expression_extractor file_to_scan html_root header_file '
          'footer_file output [package_roots+]');
    exit(0);
  }
  IoService ioService = new IoServiceImpl();

  var packageRoots =
      (args.length < 6) ? [Platform.packageRoot] : args.sublist(5);
  var sourceCrawler = new SourceCrawlerImpl(packageRoots);
  var sourceMetadataExtractor = new SourceMetadataExtractor();
  List<DirectiveInfo> directives =
      sourceMetadataExtractor.gatherDirectiveInfo(args[0], sourceCrawler);
  var htmlExtractor = new HtmlExpressionExtractor(directives);
  htmlExtractor.crawl(args[1], ioService);

  var expressions = htmlExtractor.expressions;
  expressions.add('null');

  var headerFile = args[2];
  var footerFile = args[3];
  var outputFile = args[4];
  var printer;
  if (outputFile == '--') {
    printer = stdout;
  } else {
    printer = new File(outputFile).openWrite();
  }

  // Output the header file first.
  if (headerFile != '') {
    printer.write(_readFile(headerFile));
  }

  printer.write('// Found ${expressions.length} expressions\n');
  Module module = new Module()
      ..bind(Parser, toImplementation: DynamicParser)
      ..bind(ParserBackend, toImplementation: DartGetterSetterGen);
  Injector injector =
      new DynamicInjector(modules: [module], allowImplicitInjection: true);

  runZoned(() {
    // Run the generator.
    injector.get(ParserGetterSetter).generateParser(htmlExtractor.expressions,
        printer);
  }, zoneSpecification: new ZoneSpecification(print: (_, __, ___, String line) {
    printer.write(line);
  }));


  // Output footer last.
  if (footerFile != '') {
    printer.write(_readFile(footerFile));
  }
}

String _readFile(String filePath) => new File(filePath).readAsStringSync();
