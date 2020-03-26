"""kms class for interacting with kms service

Handle selection of kms keys
TODO: handle creation of kms keys with iam capabilities
"""
import boto3
from fzfaws.utils.pyfzf import Pyfzf


class KMS:
    """kms wrapper class around boto3.client('kms')

    handles operation around kms, selection/creation etc

    Attributes:
        client: object, boto3 client
        keyid: string, the selected kms key id
    """

    def __init__(self, region=None, profile=None):
        self.client = boto3.client('kms', region_name=region)
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
