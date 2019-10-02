#################################################################
#
# File: SNSAlerter.py
#
# Author: djohnstone
#
# This file is to publish new findings to an SNS topic
#
#################################################################

import boto3
import json
from security_monkey import app
from security_monkey.alerters import custom_alerter

changed_arns = []

class SNSAlerter(object):
	__metaclass__ = custom_alerter.AlerterType

	def report_watcher_changes(self, watcher):
		# We don't need to do anything with the watcher in our alerter
		if app.config.get('SNS_ALERT_QUEUE_ARN'):
			app.logger.debug("Entering SNSAlerter.report_watcher_changes")
			for item in watcher.changed_items:
				if item.arn is not None:
					changed_arns.append(item.arn)
			for item in watcher.created_items:
				if item.arn is not None:
					changed_arns.append(item.arn)

	def report_auditor_changes(self, auditor):
		if app.config.get('SNS_ALERT_QUEUE_ARN'):
			app.logger.debug("Entering SNSAlerter.report_auditor_changes")

			toPublish = []
			for item in auditor.items:
				for issue in item.confirmed_new_issues: # to exclude ephemeral changes
					if item.arn in changed_arns:
						toPublish.append({'index': item.index, 'account': item.account, 'name': item.name, 'region': item.region, 'score': issue.score, 'issue': issue.issue, 'itemid': issue.item_id, 'notes': issue.notes, 'arn': item.arn})

			if len(toPublish) > 0:
				self.publish(toPublish)

	def publish(self, toPublish):
		snsQueue = app.config.get('SNS_ALERT_QUEUE_ARN')
		snsRegion = app.config.get('SNS_ALERT_QUEUE_REGION')
		boto3.client('sns', region_name=snsRegion).publish(TopicArn = snsQueue, Message = json.dumps(toPublish))
		app.logger.info("Published findings to SNS")
