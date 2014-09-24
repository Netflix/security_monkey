import 'package:hammock/hammock.dart';
import 'package:angular/angular.dart';
import 'dart:mirrors';

//import 'package:SecurityMonkey/model/network_whitelist_entry.dart';
import 'package:SecurityMonkey/model/Account.dart';
import 'package:SecurityMonkey/model/Issue.dart';
import 'package:SecurityMonkey/model/Item.dart';
import 'package:SecurityMonkey/model/Revision.dart';
import 'package:SecurityMonkey/util/constants.dart';

//final serializeNWL = serializer("NetworkWhitelistEntry", ["id", "name", "cidr", "notes"]);
//final deserializeNWL = deserializer(NetworkWhitelistEntry, ["id", "name", "cidr", "notes"]);
final serializeAWSAccount = serializer("accounts", ["id", "active", "third_party", "name", "s3_name", "number", "notes"]);
final serializeIssue = serializer("issues", ["id", "score", "issue", "notes", "justified", "justified_user", "justification", "justified_date", "item_id"]);
final serializeRevision = serializer("revisions", ["id", "item_id", "config", "active", "date_created", "diff_html"]);
final serializeItem = serializer("items", ["id", "technology", "region", "account", "name"]);

createHammockConfig(Injector inj) {
    return new HammockConfig(inj)
            ..set(
                {
//                "NetworkWhitelistEntry": {
//                    "type": NetworkWhitelistEntry,
//                    "serializer": serializeNWL,
//                    "deserializer": {
//                        "query": deserializeNWL
//                    }
//                },
                "accounts": {
                    "type": Account,
                    "serializer": serializeAWSAccount,
                    "deserializer": {
                        "query": deserializeAWSAccount
                    }
                },
                "issues": {
                    "type": Issue,
                    "serializer": serializeIssue,
                    "deserializer": {
                        "query": deserializeIssue
                    }
                },
                "revisions": {
                    "type": Revision,
                    "serializer": serializeRevision,
                    "deserializer": {
                        "query": deserializeRevision
                    }
                },
                "items": {
                    "type": Item,
                    "serializer": serializeItem,
                    "deserializer": {
                        "query": deserializeItem
                    }
                }
            })
            ..urlRewriter.baseUrl = '$API_HOST'
            ..requestDefaults.withCredentials = true
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

deserializeIssue(r) => new Issue.fromMap(r.content);
deserializeRevision(r) => new Revision.fromMap(r.content);
deserializeItem(r) => new Item.fromMap({"item": r.content});


//deserializer(type, attrs) {
//    print("Inside deserializer. Type: $type Attrs: $attrs");
//    return (r) {
//        print("Inside deserializer sub-ret. Type: $type Attrs: $attrs and r: $r");
//        final params = attrs.fold([], (res, attr) => res..add(r.content[attr]));
//        return reflectClass(type).newInstance(const Symbol(''), params).reflectee;
//    };
//}

class JsonApiOrgFormat extends JsonDocumentFormat {
    resourceToJson(Resource res) {
        print("Inside resourcetojson");
        //return {res.type.toString(): [res.content]};
        return res.content;
    }

    Resource jsonToResource(type, json) {
        print("Inside jsontoresource");
        return resource(type, json["id"], json);
    }

    List<Resource> jsonToManyResources(type, json) {
        if (json.containsKey('items')) {
            json[type] = json['items'];
        }
        return json[type].map((r) => resource(type, r["id"], r)).toList();
    }
}
