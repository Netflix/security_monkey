#Just a quick program to test your communication of your slack bot and security monkey
from slack_post import postMessage

type = "changedItem"
text = "Index: ec2image\n Account: test\n Region: test\n Name: test"

postMessage(text, type, "ec2", "amiImage")

type = "addedItem"
text = "Index: ec2image\n Account: test\n Region: test\n Name: test"

postMessage(text, type, "ec2", "instanceName")

type = "deletedItem"
text = "Index: ec2image\n Account: test\n Region: test\n Name: test"

postMessage(text, type, "s3", "bucketID")

