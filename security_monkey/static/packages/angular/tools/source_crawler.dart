library source_crawler;

import 'package:analyzer/src/generated/ast.dart';

typedef CompilationUnitVisitor(CompilationUnit cu);

/**
 * Dart source file crawler. As it crawls Dart source, it calls
 * [CompilationUnitVisitor] on each file.
 */
abstract class SourceCrawler {
  void crawl(String entryPoint, CompilationUnitVisitor visitor);
}
