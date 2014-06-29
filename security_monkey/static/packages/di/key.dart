library di.key;

int _lastKeyId = 0;
int get lastKeyId => _lastKeyId;

Map<int, int> _hashToKey = {};

class Key {
  final Type type;
  final Type annotation;
  final int hashCode;
  final int id;

  factory Key(Type type, [Type annotation]) {
    var _hashCode = type.hashCode + annotation.hashCode;
    var _id = _hashToKey.putIfAbsent(_hashCode, () => _lastKeyId++);
    return new Key._newKey(type, annotation, _hashCode, _id);
  }

  Key._newKey(this.type, this.annotation, this.hashCode, this.id);

  bool operator ==(other) =>
      other is Key && other.hashCode == hashCode;

  String toString() {
    String asString = type.toString();
    if (annotation != null) {
      asString += ' annotated with: ${annotation.toString()}';
    }
    return asString;
  }
}
