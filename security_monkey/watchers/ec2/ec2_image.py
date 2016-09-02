#     Copyright 2016 Bridgewater Associates
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
"""
.. module: security_monkey.watchers.ec2image
    :platform: Unix

.. version:: $$VERSION$$


"""
from security_monkey.decorators import record_exception, iter_account_region
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey import app


class EC2Image(Watcher):
    index = 'ec2image'
    i_am_singular = 'EC2 Image'
    i_am_plural = 'EC2 Images'

    def __init__(self, accounts=None, debug=False):
        super(EC2Image, self).__init__(accounts=accounts, debug=debug)

    @record_exception()
    def describe_images(self, **kwargs):
        from security_monkey.common.sts_connect import connect
        ec2 = connect(kwargs['account_name'], 'boto3.ec2.client', region=kwargs['region'],
                      assumed_role=kwargs['assumed_role'])

        response = self.wrap_aws_rate_limited_call(ec2.describe_images,
                                                   Owners=['self'])
        images = response.get('Images')
        return images

    def slurp(self):
        """
        :returns: item_list - list of available EC2 images defined by account
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()

        @iter_account_region(index=self.index, accounts=self.accounts, service_name='ec2')
        def slurp_items(**kwargs):
            item_list = []
            exception_map = {}
            kwargs['exception_map'] = exception_map
            app.logger.debug("Checking {}/{}/{}".format(self.index,
                                                        kwargs['account_name'], kwargs['region']))
            images = self.describe_images(**kwargs)

            if images:
                app.logger.debug("Found {} {}.".format(
                    len(images), self.i_am_plural))
                for image in images:
                    name = image['ImageId']
                    if self.check_ignore_list(name):
                        continue

                    item_config = {
                        'name': name,
                        'image_id': image.get('ImageId'),
                        'image_location': image.get('ImageLocation'),
                        'state': image.get('State'),
                        'owner_id': image.get('OwnerId'),
                        'creation_date': str(image.get('CreationDate')),
                        'public': image.get('Public'),
                        'root_device_name': image.get('RootDeviceName'),
                        'root_device_type': image.get('RootDeviceType'),
                        'description': image.get('Description'),
                        'block_device_mappings': image.get('BlockDeviceMappings')
                    }

                    item = EC2ImageItem(region=kwargs['region'],
                                        account=kwargs['account_name'],
                                        name=name, config=dict(item_config))

                    item_list.append(item)

            return item_list, exception_map
        return slurp_items()


class EC2ImageItem(ChangeItem):

    def __init__(self, region=None, account=None, name=None, config={}):
        super(EC2ImageItem, self).__init__(
            index=EC2Image.index,
            region=region,
            account=account,
            name=name,
            new_config=config)
