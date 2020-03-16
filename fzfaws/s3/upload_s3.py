"""handles uploading operation of s3

upload local files/directories to s3
"""
import json
from fzfaws.s3.s3 import S3


def upload_s3(args):
    """upload local files/directories to s3

    upload through boto3 s3 client

    Args:
        args: argparse args
    Returns:
        None
    """

    s3 = S3()
    s3.set_s3_bucket()
    s3.set_s3_path()

