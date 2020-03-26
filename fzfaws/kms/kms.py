"""kms class for interacting with kms service

Handle selection of kms keys
TODO: handle creation of kms keys with iam capabilities
"""
import boto3


class KMS:
    """kms wrapper class around boto3.client('kms')

    handles operation around kms, selection/creation etc

    Attributes:
        client: object, boto3 client
        keyid: string, the selected kms key id
    """

    def __init__(self, region=None, profile=None):
        self.client = boto3.client('kms', region=region, profile=profile)
        self.keyid = None

    def set_key(self):
        paginator = self.client.get_paginator('list_keys')
        for result in paginator.paginate():
            print(result)
