from security_monkey.cloudaux_watcher import CloudAuxWatcher
from security_monkey.exceptions import SecurityMonkeyException
from cloudaux.aws.s3 import list_buckets
from cloudaux.orchestration.aws.s3 import get_bucket
from security_monkey import AWS_DEFAULT_REGION


class S3(CloudAuxWatcher):
    index = 's3'
    i_am_singular = 'S3 Bucket'
    i_am_plural = 'S3 Buckets'

    def __init__(self, *args, **kwargs):
        super(S3, self).__init__(*args, **kwargs)
        self.honor_ephemerals = True
        self.ephemeral_paths = ['GrantReferences', '_version']
        self.service_name = 's3'

    def list_method(self, **kwargs):
        buckets = list_buckets(**kwargs)['Buckets']
        return [bucket['Name'] for bucket in buckets]

    def get_name_from_list_output(self, item):
        return item

    def _get_regions(self):
        return [AWS_DEFAULT_REGION]

    def get_method(self, item_name, **kwargs):
        bucket = get_bucket(item_name, **kwargs)

        if bucket and bucket.get("Error"):
            raise SecurityMonkeyException("S3 Bucket: {} fetching error: {}".format(item_name, bucket["Error"]))

        return bucket
