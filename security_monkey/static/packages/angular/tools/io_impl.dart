library angular.io_impl;

import 'dart:io';
import 'package:angular/tools/io.dart';

class IoServiceImpl implements IoService {

  String readAsStringSync(String filePath) =>
      new File(filePath).readAsStringSync();

  void visitFs(String rootDir, FsVisitor visitor) {
    Directory root = new Directory(rootDir);
    if (!FileSystemEntity.isDirectorySync(rootDir)) {
      throw 'Expected $rootDir to be a directory!';
    }
    root.listSync(recursive: true, followLinks: true).forEach((entity) {
      if (entity.statSync().type == FileSystemEntityType.FILE) {
        visitor(entity.path);
      }
    });
  }
}
