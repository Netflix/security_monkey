library selector;

import 'package:html5lib/dom.dart';

class ContainsSelector {
  final String selector;
  final RegExp regexp;

  ContainsSelector(this.selector, String regexp): regexp = new RegExp(regexp);
}

RegExp _SELECTOR_REGEXP = new RegExp(r'^(?:([\w\-]+)|(?:\.([\w\-]+))|(?:\[([\w\-\*]+)(?:=([^\]]*))?\]))');
RegExp _CONTAINS_REGEXP = new RegExp(r'^:contains\(\/(.+)\/\)$');
RegExp _ATTR_CONTAINS_REGEXP = new RegExp(r'^\[\*=\/(.+)\/\]$');

class _SelectorPart {
  final String element;
  final String className;
  final String attrName;
  final String attrValue;

  const _SelectorPart.fromElement(this.element)
      : className = null, attrName = null, attrValue = null;

  const _SelectorPart.fromClass(this.className)
      : element = null, attrName = null, attrValue = null;


  const _SelectorPart.fromAttribute(this.attrName, this.attrValue)
      : element = null, className = null;

  String toString() =>
    element == null
      ? (className == null
         ? (attrValue == '' ? '[$attrName]' : '[$attrName=$attrValue]')
         : '.$className')
      : element;
}

List<_SelectorPart> _splitCss(String selector) {
  List<_SelectorPart> parts = [];
  var remainder = selector;
  var match;
  while (!remainder.isEmpty) {
    if ((match = _SELECTOR_REGEXP.firstMatch(remainder)) != null) {
      if (match[1] != null) {
        parts.add(new _SelectorPart.fromElement(match[1].toLowerCase()));
      } else if (match[2] != null) {
        parts.add(new _SelectorPart.fromClass(match[2].toLowerCase()));
      } else if (match[3] != null) {
        var attrValue = match[4] == null ? '' : match[4].toLowerCase();
        parts.add(new _SelectorPart.fromAttribute(match[3].toLowerCase(),
                                                  attrValue));
      } else {
        throw "Missmatched RegExp $_SELECTOR_REGEXP on $remainder";
      }
    } else {
      throw "Unknown selector format '$remainder'.";
    }
    remainder = remainder.substring(match.end);
  }
  return parts;
}

bool matchesNode(Node node, String selector) {
  var match, selectorParts;
  if ((match = _CONTAINS_REGEXP.firstMatch(selector)) != null) {
    if (node is! Text) {
      return false;
    }
    return new RegExp(match.group(1)).hasMatch((node as Text).text);
  } else if ((match = _ATTR_CONTAINS_REGEXP.firstMatch(selector)) != null) {
    if (node is! Element) {
      return false;
    }
    var regexp = new RegExp(match.group(1));
    for (String attrName in node.attributes.keys) {
      if (regexp.hasMatch(node.attributes[attrName])) {
        return true;
      }
    }
    return false;
  } else if ((selectorParts = _splitCss(selector)) != null) {
    if (node is! Element) return false;
    String nodeName = (node as Element).localName.toLowerCase();

    bool stillGood = true;
    selectorParts.forEach((_SelectorPart part) {
      if (part.element != null) {
        if (nodeName != part.element) {
          stillGood = false;
        }
      } else if (part.className != null) {
        if (node.attributes['class'] == null ||
            !node.attributes['class'].split(' ').contains(part.className)) {
          stillGood = false;
        }
      } else if (part.attrName != null) {
        String matchingKey = _matchingKey(node.attributes.keys, part.attrName);
        if (matchingKey == null || part.attrValue == '' ?
              node.attributes[matchingKey] == null :
              node.attributes[matchingKey] != part.attrValue) {
          stillGood = false;
        }
      }
    });

    return stillGood;
  }

  throw new ArgumentError('Unsupported Selector: $selector');
}

String _matchingKey(Iterable keys, String attrName) =>
    keys.firstWhere(
        (key) => new RegExp('^${attrName.replaceAll('*', r'[\w\-]+')}\$').hasMatch(key.toString()),
        orElse: () => null);
