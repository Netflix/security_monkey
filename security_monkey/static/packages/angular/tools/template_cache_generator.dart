library angular.template_cache_generator;

import 'dart:io';
import 'dart:async';
import 'dart:collection';

import 'package:analyzer/src/generated/ast.dart';
import 'package:analyzer/src/generated/source.dart';
import 'package:analyzer/src/generated/element.dart';
import 'package:args/args.dart';
import 'package:di/generator.dart';

const String PACKAGE_PREFIX = 'package:';
const String DART_PACKAGE_PREFIX = 'dart:';

String fileHeader(String library) => '''// GENERATED, DO NOT EDIT!
library ${library};

import 'package:angular/angular.dart';

primeTemplateCache(TemplateCache tc) {
''';

const String FILE_FOOTER = '}';

main(List arguments) {
  Options options = parseArgs(arguments);
  if (options.verbose) {
    print('entryPoint: ${options.entryPoint}');
    print('outputLibrary: ${options.outputLibrary}');
    print('output: ${options.output}');
    print('sdk-path: ${options.sdkPath}');
    print('package-root: ${options.packageRoots.join(",")}');
    print('template-root: ${options.templateRoots.join(",")}');
    var rewrites = options.urlRewrites.keys
        .map((k) => '${k.pattern},${options.urlRewrites[k]}')
        .join(';');
    print('url-rewrites: $rewrites');
    print('skip-classes: ${options.skippedClasses.join(",")}');
  }

  Map<String, String> templates = {};

  var c = new SourceCrawler(options.sdkPath, options.packageRoots);
  var visitor = new TemplateCollectingVisitor(templates, options.skippedClasses,
      c, options.templateRoots);
  c.crawl(options.entryPoint,
      (CompilationUnitElement compilationUnit, SourceFile source) =>
          visitor(compilationUnit, source.canonicalPath));

  var sink;
  if (options.output == '-') {
    sink = stdout;
  } else {
    var f = new File(options.output)..createSync(recursive: true);
    sink = f.openWrite();
  }
  return printTemplateCache(
      templates, options.urlRewrites, options.outputLibrary, sink)
      .then((_) => sink.flush());
}

class Options {
  String entryPoint;
  String outputLibrary;
  String sdkPath;
  List<String> packageRoots;
  List<String> templateRoots;
  String output;
  Map<RegExp, String> urlRewrites;
  Set<String> skippedClasses;
  bool verbose;
}

Options parseArgs(List arguments) {
  var parser = new ArgParser()
      ..addOption('sdk-path', abbr: 's',
          defaultsTo: Platform.environment['DART_SDK'],
          help: 'Dart SDK Path')
      ..addOption('package-root', abbr: 'p', defaultsTo: Platform.packageRoot,
          help: 'comma-separated list of package roots')
      ..addOption('template-root', abbr: 't', defaultsTo: '.',
          help: 'comma-separated list of paths from which templates with'
                'absolute paths can be fetched')
      ..addOption('out', abbr: 'o', defaultsTo: '-',
          help: 'output file or "-" for stdout')
      ..addOption('url-rewrites', abbr: 'u',
          help: 'semicolon-separated list of URL rewrite rules, of the form: '
                'patternUrl,rewriteTo')
      ..addOption('skip-classes', abbr: 'b',
          help: 'comma-separated list of classes to skip templating')
      ..addFlag('verbose', abbr: 'v', help: 'verbose output')
      ..addFlag('help', abbr: 'h', negatable: false, help: 'show this help');

  printUsage() {
    print('Usage: dart template_cache_generator.dart '
          '--sdk-path=path [OPTION...] entryPoint libraryName');
    print(parser.getUsage());
  }

  fail(message) {
    print('Error: $message\n');
    printUsage();
    exit(1);
  }

  var args;
  try {
    args = parser.parse(arguments);
  } catch (e) {
    fail('failed to parse arguments');
  }

  if (args['help']) {
    printUsage();
    exit(0);
  }

  if (args['sdk-path'] == null) {
    fail('--sdk-path must be specified');
  }

  var options = new Options();
  options.sdkPath = args['sdk-path'];
  options.packageRoots = args['package-root'].split(',');
  options.templateRoots = args['template-root'].split(',');
  options.output = args['out'];
  if (args['url-rewrites'] != null) {
    options.urlRewrites = new LinkedHashMap.fromIterable(
        args['url-rewrites'].split(';').map((p) => p.split(',')),
        key:   (p) => new RegExp(p[0]),
        value: (p) => p[1]);
  } else {
    options.urlRewrites = {};
  }
  if (args['skip-classes'] != null) {
    options.skippedClasses = new Set.from(args['skip-classes'].split(','));
  } else {
    options.skippedClasses = new Set();
  }
  options.verbose = args['verbose'];
  if (args.rest.length != 2) {
    fail('unexpected arguments: ${args.rest.join(' ')}');
  }
  options.entryPoint = args.rest[0];
  options.outputLibrary = args.rest[1];
  return options;
}

printTemplateCache(Map<String, String> templateKeyMap,
                        Map<RegExp, String> urlRewriters,
                        String outputLibrary,
                        IOSink outSink) {

  outSink.write(fileHeader(outputLibrary));

  Future future = new Future.value(0);
  List uris = templateKeyMap.keys.toList()..sort()..forEach((uri) {
    var templateFile = templateKeyMap[uri];
    future = future.then((_) {
      return new File(templateFile).readAsString().then((fileStr) {
        fileStr = fileStr.replaceAll('"""', r'\"\"\"');
        String resultUri = uri;
        urlRewriters.forEach((regexp, replacement) {
          resultUri = resultUri.replaceFirst(regexp, replacement);
        });
        outSink.write(
            'tc.put("$resultUri", new HttpResponse(200, r"""$fileStr"""));\n');
      });
    });
  });

  // Wait until all templates files are processed.
  return future.then((_) {
    outSink.write(FILE_FOOTER);
  });
}

class TemplateCollectingVisitor {
  Map<String, String> templates;
  Set<String> skippedClasses;
  SourceCrawler sourceCrawler;
  List<String> templateRoots;

  TemplateCollectingVisitor(this.templates, this.skippedClasses,
      this.sourceCrawler, this.templateRoots);

  void call(CompilationUnitElement cue, String srcPath) {
    processDeclarations(cue, srcPath);

    cue.enclosingElement.parts.forEach((CompilationUnitElement part) {
      processDeclarations(part, srcPath);
    });
  }

  void processDeclarations(CompilationUnitElement cue, String srcPath) {
    CompilationUnit cu = sourceCrawler.context
        .resolveCompilationUnit(cue.source, cue.library);
    cu.declarations.forEach((CompilationUnitMember declaration) {
      // We only care about classes.
      if (declaration is! ClassDeclaration) return;
      ClassDeclaration clazz = declaration;
      List<String> cacheUris = [];
      bool cache = true;
      clazz.metadata.forEach((Annotation ann) {
        if (ann.arguments == null) return; // Ignore non-class annotations.
        if (skippedClasses.contains(clazz.name.name)) return;

        switch (ann.name.name) {
          case 'Component':
              extractComponentMetadata(ann, cacheUris); break;
          case 'NgTemplateCache':
              cache = extractNgTemplateCache(ann, cacheUris); break;
        }
      });
      if (cache && cacheUris.isNotEmpty) {
        Source currentSrcDir = sourceCrawler.context.sourceFactory
            .resolveUri(null, 'file://$srcPath');
        cacheUris..sort()..forEach(
            (uri) => storeUriAsset(uri, currentSrcDir, templateRoots));
      }
    });
  }

  void extractComponentMetadata(Annotation ann, List<String> cacheUris) {
    ann.arguments.arguments.forEach((Expression arg) {
      if (arg is NamedExpression) {
        NamedExpression namedArg = arg;
        var paramName = namedArg.name.label.name;
        if (paramName == 'templateUrl') {
          cacheUris.add(assertString(namedArg.expression).stringValue);
        } else if (paramName == 'cssUrl') {
          if (namedArg.expression is StringLiteral) {
            cacheUris.add(assertString(namedArg.expression).stringValue);
          } else {
            cacheUris.addAll(assertList(namedArg.expression).elements.map((e) =>
                assertString(e).stringValue));
          }
        }
      }
    });
  }

  bool extractNgTemplateCache(Annotation ann, List<String> cacheUris) {
    bool cache = true;
    ann.arguments.arguments.forEach((Expression arg) {
      if (arg is NamedExpression) {
        NamedExpression namedArg = arg;
        var paramName = namedArg.name.label.name;
        if (paramName == 'preCacheUrls') {
          assertList(namedArg.expression).elements
            ..forEach((expression) =>
                cacheUris.add(assertString(expression).stringValue));
        }
        if (paramName == 'cache') {
          cache = assertBoolean(namedArg.expression).value;
        }
      }
    });
    return cache;
  }

  void storeUriAsset(String uri, Source srcPath, templateRoots) {
    String assetFileLocation = findAssetLocation(uri, srcPath, templateRoots);
    if (assetFileLocation == null) {
      print("Could not find asset for uri: $uri");
    } else {
      templates[uri] = assetFileLocation;
    }
  }

  String findAssetLocation(String uri, Source srcPath, List<String>
      templateRoots) {
    if (uri.startsWith('/')) {
      var paths = templateRoots.map((r) => '$r/$uri');
      return paths.firstWhere((p) => new File(p).existsSync(),
          orElse: () => paths.first);
    }
    // Otherwise let the sourceFactory resolve for packages, and relative paths.
    Source source = sourceCrawler.context.sourceFactory
        .resolveUri(srcPath, uri);
    return (source != null) ? source.fullName : null;
  }

  BooleanLiteral assertBoolean(Expression key) {
    if (key is! BooleanLiteral) {
        throw 'must be a boolean literal: ${key.runtimeType}';
    }
    return key;
  }

  ListLiteral assertList(Expression key) {
    if (key is! ListLiteral) {
        throw 'must be a list literal: ${key.runtimeType}';
    }
    return key;
  }

  StringLiteral assertString(Expression key) {
    if (key is! StringLiteral) {
        throw 'must be a string literal: ${key.runtimeType}';
    }
    return key;
  }
}
