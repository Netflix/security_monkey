part of angular.mock;

String depth = '';

ENTER(name) {
  dump('${depth}ENTER: $name');
  depth = depth +  '  ';
}

LEAVE(name) {
  depth = depth.substring(0, depth.length -2);
  dump('${depth}LEAVE: $name');
}

MARK(name) {
  dump('$depth$name');
}


dump([p1, p2, p3, p4, p5, p6, p7, p8, p9, p10]) {
  var log = [];
  if (p1 != null) log.add(STRINGIFY(p1));
  if (p2 != null) log.add(STRINGIFY(p2));
  if (p3 != null) log.add(STRINGIFY(p3));
  if (p4 != null) log.add(STRINGIFY(p4));
  if (p5 != null) log.add(STRINGIFY(p5));
  if (p6 != null) log.add(STRINGIFY(p6));
  if (p7 != null) log.add(STRINGIFY(p7));
  if (p8 != null) log.add(STRINGIFY(p8));
  if (p9 != null) log.add(STRINGIFY(p9));
  if (p10 != null) log.add(STRINGIFY(p10));
  js.context['console'].callMethod('log', [log.join(', ')]);
}

STRINGIFY(obj) {
  if (obj is List) {
    var out = [];
    obj.forEach((i) => out.add(STRINGIFY(i)));
    return '[${out.join(", ")}]';
  } else if (obj is Comment) {
    return '<!--${obj.text}-->';
  } else if (obj is Element) {
    return obj.outerHtml;
  } else if (obj is String) {
    return '"$obj"';
  } else {
    return obj.toString();
  }
}
