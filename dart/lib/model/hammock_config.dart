import 'package:hammock/hammock.dart';
import 'package:angular/angular.dart';
import 'dart:mirrors';

import 'package:SecurityMonkey/model/network_whitelist_entry.dart';
import 'package:SecurityMonkey/model/Account.dart';
import 'package:SecurityMonkey/util/constants.dart';

final serializeNWL = serializer("NetworkWhitelistEntry", ["id", "name", "cidr", "notes"]);
final deserializeNWL = deserializer(NetworkWhitelistEntry, ["id", "name", "cidr", "notes"]);
final serializeAWSAccount = serializer("accounts", ["id", "active", "third_party", "name", "s3_name", "number", "notes"]);

createHammockConfig(Injector inj) {
  return new HammockConfig(inj)
      ..set(
          {
          "NetworkWhitelistEntry" : {
              "type" : NetworkWhitelistEntry,
              "serializer" : serializeNWL,
              "deserializer": {"query" : deserializeNWL}
          },
          "accounts" : {
              "type" : Account,
              "serializer" : serializeAWSAccount,
              "deserializer": {"query" : deserializeAWSAccount}
          }
      })
      ..urlRewriter.baseUrl = '$API_HOST'
      ..urlRewriter.suffix = '/'
      ..requestDefaults.withCredentials=true
      ..documentFormat = new JsonApiOrgFormat();
}

serializer(type, attrs) {
  print("Inside serializer. Type: $type Attrs: $attrs");
  return (obj) {
    print("Inside serializer sub-ret. Type: $type Attrs: $attrs");
    final m = reflect(obj);

    final id = m.getField(#id).reflectee;
    final content = attrs.fold({}, (res, attr) {
      res[attr] = m.getField(new Symbol(attr)).reflectee;
      return res;
    });

    return resource(type, id, content);
  };
}

deserializeAWSAccount(r) => new Account()
  ..id = r.id
  ..active = r.content['active']
  ..third_party = r.content['third_party']
  ..name = r.content['name']
  ..s3_name = r.content['s3_name']
  ..number = r.content['number']
  ..notes = r.content['notes'];
  

deserializer(type, attrs) {
  print("Inside deserializer. Type: $type Attrs: $attrs");
  return (r) {
    print("Inside deserializer sub-ret. Type: $type Attrs: $attrs and r: $r");
    final params = attrs.fold([], (res, attr) => res..add(r.content[attr]));
    return reflectClass(type).newInstance(const Symbol(''), params).reflectee;
  };
}

class JsonApiOrgFormat extends JsonDocumentFormat {
  resourceToJson(Resource res) {
      return {res.type.toString(): [res.content]};
  }

  Resource jsonToResource(type, json) {
      return resource(type, json[type][0]["id"], json[type][0]);
  }

  List<Resource> jsonToManyResources(type, json) {
      json[type] = json['items'];
      return json[type].map((r) => resource(type, r["id"], r));
  }
}