library link_matcher;

import 'dart:html';

const _TARGETS = const ['_blank', '_parent', '_self', '_top'];

/**
 * RouterLinkMatcher is used to customize [Router] behavior by
 * selecting which [AnchorElement]s to process.
 */
abstract class RouterLinkMatcher {
  bool matches(AnchorElement link);
}

/**
 * A [RouterLinkMatcher] that matches anchor elements which
 * do not have have `_blank`, `_parent`, `_self` or `_top`
 * set as target.
 */
class DefaultRouterLinkMatcher implements RouterLinkMatcher {
  bool matches(AnchorElement link) => !_TARGETS.contains(link.target);
}
