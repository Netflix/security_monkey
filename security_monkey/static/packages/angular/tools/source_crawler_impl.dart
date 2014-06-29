library angular.source_crawler_impl;

import 'dart:io';
import 'package:analyzer/analyzer.dart';
import 'package:angular/tools/source_crawler.dart';

const String PACKAGE_PREFIX = 'package:';

/**
 * Dart source file crawler. As it crawls Dart source, it calls
 * [CompilationUnitVisitor] on each file.
 */
class SourceCrawlerImpl implements SourceCrawler {
  final List<String> packageRoots;

  SourceCrawlerImpl(this.packageRoots);

  void crawl(String entryPoint, CompilationUnitVisitor visitor) {
    List<String> visited = <String>[];
    List<String> toVisit = <String>[];
    if (entryPoint.startsWith(PACKAGE_PREFIX)) {
      var path = resolvePackagePath(entryPoint);
      if (path == null) {
        throw 'Unable to resolve $entryPoint';
      }
      toVisit.add(path);
    } else {
      toVisit.add(entryPoint);
    }

    while (toVisit.isNotEmpty) {
      var currentFile = toVisit.removeAt(0);
      visited.add(currentFile);
      var file = new File(currentFile);
      // Possible source file doesn't exist. For example if it is generated.
      if (!file.existsSync()) continue;
      var currentDir = file.parent.path;
      CompilationUnit cu = parseDartFile(currentFile);
      processImports(cu, currentDir, currentFile, visited, toVisit);
      visitor(cu);
    }
  }

  void processImports(CompilationUnit cu, String currentDir,
                      String currentFile, List<String> visited,
                      List<String> toVisit) {
    cu.directives.forEach((Directive directive) {
      if (directive is ImportDirective ||
          directive is PartDirective ||
          directive is ExportDirective) {
        UriBasedDirective import = directive;
        String canonicalFile = canonicalizeImportPath(
            currentDir, currentFile, import.uri.stringValue);
        if (canonicalFile == null) return;
        if (!visited.contains(canonicalFile) &&
            !toVisit.contains(canonicalFile)) {
          toVisit.add(canonicalFile);
        }
      }
    });
  }

  String canonicalizeImportPath(String currentDir,
                                String currentFile,
                                String uri) {
    // ignore core libraries
    if (uri.startsWith('dart:')) {
      return null;
    }
    if (uri.startsWith(PACKAGE_PREFIX)) {
      return resolvePackagePath(uri);
    }
    // relative import.
    if (uri.startsWith('../')) {
      while (uri.startsWith('../')) {
        uri = uri.substring('../'.length);
        currentDir = currentDir.substring(0, currentDir.lastIndexOf('/'));
      }
    }
    return '$currentDir/$uri';
  }

  String resolvePackagePath(String uri) {
    for (String packageRoot in packageRoots) {
      var resolvedPath = _packageUriResolver(uri, packageRoot);
      if (new File(resolvedPath).existsSync()) {
        return resolvedPath;
      }
    }
    return null;
  }

  String _packageUriResolver(String uri, String packageRoot) {
    var packagePath = uri.substring(PACKAGE_PREFIX.length);
    if (!packageRoot.endsWith('/')) {
      packageRoot = packageRoot + '/';
    }
    return packageRoot + packagePath;
  }
}
