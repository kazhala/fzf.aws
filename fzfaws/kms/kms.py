"""kms class for interacting with kms service

Handle selection of kms keys
TODO: handle creation of kms keys with iam capabilities
"""
import boto3
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.session import BaseSession


class KMS(BaseSession):
    """kms wrapper class around boto3.client('kms')

    handles operation around kms, selection/creation etc

    Attributes:
        region: region for the operation
        profile: profile to use for the operation
        client: initialized boto3 client with region and profile in use
        resource: initialized boto3 resource with region and profile in use
        keyid: string, the selected kms key id
    """

    def __init__(self, profile=None, region=None):
        super().__init__(profile=profile, region=region, service_name='kms')
        self.keyid = None

    def set_keyid(self):
        """set the key for kms using fzf"""
        fzf = Pyfzf()
        paginator = self.client.get_paginator('list_aliases')
        for result in paginator.paginate():
            aliases = [alias for alias in result.get(
                'Aliases') if alias.get('TargetKeyId')]
            fzf.process_list(aliases, 'TargetKeyId', 'AliasName', 'AliasArn')
        self.keyid = fzf.execute_fzf()
