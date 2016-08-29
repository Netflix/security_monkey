library security_monkey.model_cloudtrail;

import 'dart:convert';
import 'package:security_monkey/util/utils.dart' show localDateFromAPIDate;

class CloudTrail {
  String event_source;
  String event_name;
  DateTime event_time;
  String user_identity_arn;
  String user_agent;
  String source_ip;
  String request_parameters;
  String response_elements;
  String full_config;
  String error_code;
  String error_message;
  bool display_full_config = false;
  var encoder = new JsonEncoder.withIndent("  ");

  CloudTrail.fromMap(Map<String, Object> data) {
    full_config = encoder.convert(data);
    event_source = data['eventSource'];
    event_name = data['eventName'];

    if (data.containsKey('eventTime')) {
        if (data['eventTime'] != null) {
            event_time = localDateFromAPIDate(data['eventTime']);
        }
    }

    user_identity_arn = data['userIdentity']['arn'];
    user_agent = data['userAgent'];
    source_ip = data['sourceIPAddress'];
    request_parameters = encoder.convert(data['requestParameters']);
    response_elements = encoder.convert(data['responseElements']);
    error_code = data['errorCode'];
    error_message = data['errorMessage'];

  }

  void toggle_display_full_config() {
    display_full_config = !display_full_config;
  }

  bool is_error() {
    if (error_code == null) {
      return false;
    }
    return true;
  }

  String class_for_panel() {
    if (is_error()) {
      return "panel-danger";
    }
    return "panel-info";
  }

  String summary() {
    if (event_source != null && event_name != null) {
      String tech = '';
      if (event_source.contains('.')) {
        tech = event_source.split('.')[0];
      } else {
        tech = event_source;
      }
      return "$tech:$event_name";
    }
    return '';
  }
}