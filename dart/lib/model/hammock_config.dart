import 'package:hammock/hammock.dart';
import 'package:angular/angular.dart';
import 'dart:mirrors';

import 'network_whitelist_entry.dart';
import 'Account.dart';
import 'Issue.dart';
import 'Item.dart';
import 'Revision.dart';
import 'RevisionComment.dart';
import 'ItemComment.dart';
import 'UserSetting.dart';
import 'ignore_entry.dart';
import 'auditorsetting.dart';
import 'package:security_monkey/util/constants.dart';

//final serializeNWL = serializer("NetworkWhitelistEntry", ["id", "name", "cidr", "notes"]);
//final deserializeNWL = deserializer(NetworkWhitelistEntry, ["id", "name", "cidr", "notes"]);
final serializeAWSAccount = serializer("accounts", ["id", "active", "third_party", "name", "s3_name", "number", "notes"]);
final serializeIssue = serializer("issues", ["id", "score", "issue", "notes", "justified", "justified_user", "justification", "justified_date", "item_id"]);
final serializeRevision = serializer("revisions", ["id", "item_id", "config", "active", "date_created", "diff_html"]);
final serializeItem = serializer("items", ["id", "technology", "region", "account", "name"]);
final serializeRevisionComment = serializer("comments", ["text"]);
final serializeItemComment = serializer("comments", ["text"]);
final serializeUserSetting = serializer("settings", ["daily_audit_email", "change_report_setting", "accounts"]);
final serializeNetworkWhitelistEntry = serializer("whitelistcidrs", ["id", "name", "notes", "cidr"]);
final serializeIgnoreListEntry = serializer("ignorelistentries", ["id", "prefix", "notes", "technology"]);
final serializeAuditorSettingEntry = serializer("auditorsettings", ["account", "technology", "issue", "count", "disabled", "id"]);

createHammockConfig(Injector inj) {
    return new HammockConfig(inj)
            ..set({
                "whitelistcidrs": {
                    "type": NetworkWhitelistEntry,
                    "serializer": serializeNetworkWhitelistEntry,
                    "deserializer": {
                        "query": deserializeNetworkWhitelistEntry
                    }
                },
                "ignorelistentries": {
                    "type": IgnoreEntry,
                    "serializer": serializeIgnoreListEntry,
                    "deserializer": {
                        "query": deserializeIgnoreListEntry
                    }
                },
                "auditorsettings": {
                    "type": AuditorSetting,
                    "serializer": serializeAuditorSettingEntry,
                    "deserializer": {
                        "query": deserializeAuditorSettingEntry
                    }
                },
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
                "revision_comments": {
                    "type": RevisionComment,
                    "serializer": serializeRevisionComment,
                    "deserializer": {
                        "query": deserializeRevisionComment
                    }
                },
                "items": {
                    "type": Item,
                    "serializer": serializeItem,
                    "deserializer": {
                        "query": deserializeItem
                    }
                },
                "item_comments": {
                    "type": ItemComment,
                    "serializer": serializeItemComment,
                    "deserializer": {
                        "query": deserializeItemComment
                    }
                },
                "settings": {
                    "type": UserSetting,
                    "serializer": serializeUserSetting,
                    "deserializer": {
                        "query": deserializeUserSetting
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
deserializeRevisionComment(r) => new RevisionComment.fromMap(r.content);
deserializeItemComment(r) => new ItemComment.fromMap(r.content);
deserializeUserSetting(r) => new UserSetting.fromMap(r.content);
deserializeNetworkWhitelistEntry(r) => new NetworkWhitelistEntry.fromMap(r.content);
deserializeIgnoreListEntry(r) => new IgnoreEntry.fromMap(r.content);
deserializeAuditorSettingEntry(r) => new AuditorSetting.fromMap(r.content);

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
