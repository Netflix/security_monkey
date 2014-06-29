library di.transformers.refactor;

import 'package:analyzer/src/generated/ast.dart';
import 'package:analyzer/src/generated/element.dart';
import 'package:barback/barback.dart';
import 'package:code_transformers/resolver.dart';
import 'package:source_maps/refactor.dart';


/// Transforms all simple identifiers of [identifier] to be
/// [importPrefix].[replacement] in the entry point of the application.
///
/// When the identifier is replaced, this function also adds a prefixed import
/// of the form `import "[importUrl]" as [importPrefix]`.
///
/// This will resolve the full name of [identifier] and warn if it cannot be
/// resolved. This will only modify the main entry point of the application and
/// will not traverse into parts.
void transformIdentifiers(Transform transform, Resolver resolver,
    {String identifier, String replacement, String importUrl,
    String importPrefix}) {

  var identifierElement = resolver.getLibraryVariable(identifier);
  if (identifierElement != null) {
    identifierElement = identifierElement.getter;
  } else {
    identifierElement = resolver.getLibraryFunction(identifier);
  }

  if (identifierElement == null) {
    // TODO(blois) enable once on barback 0.12.0
    // transform.logger.fine('Unable to resolve $identifier, not '
    //     'transforming entry point.');
    transform.addOutput(transform.primaryInput);
    return;
  }

  var lib = resolver.getLibrary(transform.primaryInput.id);
  var transaction = resolver.createTextEditTransaction(lib);
  var unit = lib.definingCompilationUnit.node;

  unit.accept(new _IdentifierTransformer(transaction, identifierElement,
      '$importPrefix.$replacement', transform.logger));

  if (transaction.hasEdits) {
    _addImport(transaction, unit, importUrl, importPrefix);
  }
  _commitTransaction(transaction, transform);
}

/// Commits the transaction if there have been edits, otherwise just adds
/// the input as an output.
void _commitTransaction(TextEditTransaction transaction, Transform transform) {
  var id = transform.primaryInput.id;

  if (transaction.hasEdits) {
    var printer = transaction.commit();
    var url = id.path.startsWith('lib/')
        ? 'package:${id.package}/${id.path.substring(4)}' : id.path;
    printer.build(url);
    transform.addOutput(new Asset.fromString(id, printer.text));
  } else {
    // No modifications, so just pass the source through.
    transform.addOutput(transform.primaryInput);
  }
}

/// Injects an import into the list of imports in the file.
void _addImport(TextEditTransaction transaction, CompilationUnit unit,
    String uri, String prefix) {
  var libDirective;
  for (var directive in unit.directives) {
    if (directive is ImportDirective) {
      transaction.edit(directive.keyword.offset, directive.keyword.offset,
          'import \'$uri\' as $prefix;\n');
      return;
    } else if (directive is LibraryDirective) {
      libDirective = directive;
    }
  }

  // No imports, add after the library directive if there was one.
  if (libDirective != null) {
    transaction.edit(libDirective.endToken.offset + 2,
        libDirective.endToken.offset + 2,
        'import \'$uri\' as $prefix;\n');
  }
}

/// Vistior which changes every reference to a resolved element to a specific
/// string value.
class _IdentifierTransformer extends GeneralizingAstVisitor {
  final TextEditTransaction transaction;
  /// The element which all references to should be replaced.
  final Element original;
  /// The text which should replace [original].
  final String replacement;
  /// The current logger.
  final TransformLogger logger;

  _IdentifierTransformer(this.transaction, this.original, this.replacement,
      this.logger);

  visitIdentifier(Identifier node) {
    if (node.bestElement == original) {
      transaction.edit(node.beginToken.offset, node.endToken.end, replacement);
      return;
    }

    super.visitIdentifier(node);
  }

  // Top-level methods are not treated as prefixed identifiers, so handle those
  // here.
  visitMethodInvocation(MethodInvocation m) {
    if (m.methodName.bestElement == original) {
      if (m.target is SimpleIdentifier) {
        // Include the prefix in the rename.
        transaction.edit(m.target.beginToken.offset, m.methodName.endToken.end,
            replacement);
      } else {
        transaction.edit(m.methodName.beginToken.offset,
            m.methodName.endToken.end, replacement);
      }
      return;
    }
    super.visitMethodInvocation(m);
  }

  // Skip the contents of imports/exports/parts
  visitUriBasedDirective(ImportDirective d) {}

  visitPartDirective(PartDirective node) {
    logger.warning('Not transforming code within ${node.uri}.');
  }
}
