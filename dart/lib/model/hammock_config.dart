import 'package:hammock/hammock.dart';
import 'package:angular/angular.dart';
import 'dart:mirrors';

//import 'network_whitelist_entry.dart';
import 'Account.dart';
import 'Issue.dart';
import 'Item.dart';
import 'Revision.dart';
import 'package:security_monkey/util/constants.dart';

//final serializeNWL = serializer("NetworkWhitelistEntry", ["id", "name", "cidr", "notes"]);
//final deserializeNWL = deserializer(NetworkWhitelistEntry, ["id", "name", "cidr", "notes"]);
final serializeAWSAccount = serializer("accounts", ["id", "active", "third_party", "name", "s3_name", "number", "notes"]);
final serializeIssue = serializer("issues", ["id", "score", "issue", "notes", "justified", "justified_user", "justification", "justified_date", "item_id"]);
final serializeRevision = serializer("revisions", ["id", "item_id", "config", "active", "date_created", "diff_html"]);
final serializeItem = serializer("items", ["id", "technology", "region", "account", "name"]);

createHammockConfig(Injector inj) {
    return new HammockConfig(inj)
            ..set({
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
    return (obj) {
        final m = reflect(obj);

        final id = m.getField(#id).reflectee;
        final content = attrs.fold({}, (res, attr) {
            res[attr] = m.getField(new Symbol(attr)).reflectee;
            return res;
        });

        return resource(type, id, content);
    };
}

deserializeAWSAccount(r) => new Account.fromMap(r.content);
deserializeIssue(r) => new Issue.fromMap(r.content);
deserializeRevision(r) => new Revision.fromMap(r.content);
deserializeItem(r) => new Item.fromMap(r.content);

class JsonApiOrgFormat extends JsonDocumentFormat {
    resourceToJson(Resource res) {
        return res.content;
    }

    Resource jsonToResource(type, json) {
        return resource(type, json["id"], json);
    }

    QueryResult<Resource> jsonToManyResources(type, json) {
        Map pagination = {};
        for (var key in json.keys) {
            if (key != 'items') {
                pagination[key] = json[key];
            }
        }

        if (json.containsKey('items')) {
            json[type] = json['items'];
        }
        return new QueryResult(json[type].map((r) => resource(type, r["id"], r)).toList(), pagination);
    }
}
