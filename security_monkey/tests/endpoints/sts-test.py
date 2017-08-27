import boto3

client = boto3.client('sts')
ar = client.assume_role(RoleArn="arn:aws-cn:iam::<INSERT_YOUR_ACCOUNT_ID_HERE>:role/SecurityMonkey", RoleSessionName="test")

print(ar)