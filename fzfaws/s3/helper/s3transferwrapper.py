"""s3 transfer wrapper class

used to process env transfer config
"""
import os
import json
from s3transfer import S3Transfer, TransferConfig


class S3TransferWrapper:
    """s3 transfer wrapper class to handle transfer config

    used to handle create a s3transfer instance with user
    defined transfer configuration

    :param client: s3 client
    :type client: boto3.client
    """

    def __init__(self, client=None):
        raw_transfer_config = json.loads(os.getenv("FZFAWS_S3_TRANSFER", "{}"))
        self.transfer_config = TransferConfig(**raw_transfer_config)
        if client:
            self.s3transfer = S3Transfer(client, config=self.transfer_config)
