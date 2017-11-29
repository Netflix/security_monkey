from security_monkey.cloudaux_watcher import CloudAuxWatcher
from cloudaux.aws.ec2 import describe_images
from cloudaux.orchestration.aws.image import get_image


class EC2Image(CloudAuxWatcher):
    index = 'ec2image'
    i_am_singular = 'EC2 Image'
    i_am_plural = 'EC2 Images'
    honor_ephemerals = False
    ephemeral_paths = ['_version']
    service_name = 'ec2'

    def get_name_from_list_output(self, item):
        return item['ImageId']

    def list_method(self, **kwargs):
        return describe_images(
                Filters=[
                    # {'Name': 'is-public', 'Values': ['true']},
                    {'Name': 'owner-id', 'Values': [kwargs['account_number']]}],
                **kwargs)

    def get_method(self, item, **kwargs):
        return get_image(item['ImageId'], **kwargs)
