library angular.io;

typedef FsVisitor(String file);

/**
 * A simple mockable wrapper around dart:io that can be used without introducing
 * direct dependencies on dart:io.
 */
abstract class IoService {

  String readAsStringSync(String filePath);

  void visitFs(String rootDir, FsVisitor visitor);
}