library security_monkey.techmethods;

class TechMethods {
  List<String> technologies = new List<String>();
  Map<String, List<String>> methods = new Map<String, List<String>>();

  TechMethods();

  TechMethods.fromMap(Map data) {
    if (data.containsKey('tech_methods')) {
      var tech_methods = data['tech_methods'];
      tech_methods.forEach((k,v) => this._addToLists(k, v));
    }
  }

  void _addToLists(k, v) {
    technologies.add(k);
    methods[k] = v;
  }
}
