from security_monkey.cloudaux_watcher import CloudAuxWatcher
from security_monkey import AWS_DEFAULT_REGION
from cloudaux.aws.iam import list_saml_providers
from cloudaux.orchestration.aws.iam.saml_provider import get_saml_provider


class SAMLProvider(CloudAuxWatcher):
    index = 'samlprovider'
    i_am_singular = 'SAML Provider'
    i_am_plural = 'SAML Providers'
    honor_ephemerals = False
    ephemeral_paths = ['_version']
    override_region = 'universal'

    def get_name_from_list_output(self, item):
        # Extract the name from the ARN
        return item['Arn'].split('/')[-1]

    def _get_regions(self):
        return [AWS_DEFAULT_REGION]

    def list_method(self, **kwargs):
        return list_saml_providers(**kwargs)

    def get_method(self, item, **kwargs):
        return get_saml_provider(item, **kwargs)
