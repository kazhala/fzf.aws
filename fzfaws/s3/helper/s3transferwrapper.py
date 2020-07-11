"""Module contains the s3 transfer wrapper."""
import json
import os

from boto3.s3.transfer import S3Transfer, TransferConfig


class S3TransferWrapper:
    """A s3 transfer wrapper class to handle transfer config.

    Used to handle create a s3transfer instance with user
    defined transfer configuration.

    :param client: s3 client
    :type client: boto3.client
    """

    def __init__(self, client=None):
        """Construct wrapper instance."""
        raw_transfer_config = json.loads(os.getenv("FZFAWS_S3_TRANSFER", "{}"))
        self.transfer_config = TransferConfig(**raw_transfer_config)
        if client:
            self.s3transfer = S3Transfer(client, config=self.transfer_config)
