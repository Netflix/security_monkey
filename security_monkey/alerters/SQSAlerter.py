#################################################################
#
# File: SQSAlerter.py
#
# Author: djohnstone
#
# This file is to publish new findings to an SQS queue
#
#################################################################

import boto3
import json
from security_monkey import app
from security_monkey.alerters import custom_alerter

changed_arns = []

class SQSAlerter(object):
	__metaclass__ = custom_alerter.AlerterType

	def report_watcher_changes(self, watcher):
		# We don't need to do anything with the watcher in our alerter
		if app.config.get('SQS_ALERT_QUEUE_URL'):
			app.logger.debug("Entering SQSAlerter.report_watcher_changes")
			for item in watcher.changed_items:
				if item.arn is not None:
					changed_arns.append(item.arn)

	def report_auditor_changes(self, auditor):
		if app.config.get('SQS_ALERT_QUEUE_URL'):
			app.logger.debug("Entering SQSAlerter.report_auditor_changes")

			toPublish = []
			for item in auditor.items:
				for issue in item.confirmed_new_issues:
					if item.arn in changed_arns:
						toPublish.append({'index': item.index, 'account': item.account, 'name': item.name, 'region': item.region, 'score': issue.score, 'issue': issue.issue, 'itemid': issue.item_id, 'notes': issue.notes})

			if len(toPublish) > 0:
				self.publish(toPublish)

	def publish(self, toPublish):
		sqsQueue = app.config.get('SQS_ALERT_QUEUE_URL')
		sqsRegion = app.config.get('SQS_ALERT_QUEUE_REGION')
		boto3.client('sqs', region_name=sqsRegion).send_message(QueueUrl = sqsQueue, MessageBody = json.dumps(toPublish))
		app.logger.info("Published findings to SQS")
