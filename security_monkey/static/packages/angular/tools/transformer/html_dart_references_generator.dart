library angular.tools.transformer.html_dart_references_generator;

import 'dart:async';
import 'package:angular/tools/transformer/options.dart';
import 'package:barback/barback.dart';
import 'package:code_transformers/assets.dart';
import 'package:html5lib/parser.dart' as html5;

/// Helper which allows subsequent transformers to know what HTML files are
/// referencing a Dart file.
///
/// Currently this only allows a single HTML file to be referencing a Dart file.
class HtmlDartReferencesGenerator extends Transformer {
  final TransformOptions options;

  HtmlDartReferencesGenerator(this.options);

  // Accept all HTML files.
  String get allowedExtensions => '.html';

  Future apply(Transform transform) {
    var logger = transform.logger;
    var asset = transform.primaryInput;
    transform.addOutput(asset);

    return asset.readAsString().then((contents) {
      var document = html5.parse(contents);
      for (var tag in document.querySelectorAll('script')) {
        if (tag.attributes['type'] != 'application/dart') continue;

        var src = tag.attributes['src'];
        if (src == null) continue;

        var dartAssetId = uriToAssetId(asset.id, src, logger, tag.sourceSpan);
        if (dartAssetId == null) continue;

        var htmlRefId = new AssetId(dartAssetId.package,
              dartAssetId.path + '.html_reference');

        return transform.readInputAsString(htmlRefId).then((contents) {
          logger.error('Expected $dartAssetId to be referenced by a single '
              'HTML file, was referenced by $contents and ${asset.id}.');
        }, onError: (e) {
          transform.addOutput(
              new Asset.fromString(htmlRefId, asset.id.path));
        });
      }
    });
  }
}
