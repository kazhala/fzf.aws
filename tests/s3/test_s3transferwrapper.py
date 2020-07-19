import unittest
from fzfaws.utils import FileLoader
from fzfaws.s3.helper.s3transferwrapper import S3TransferWrapper
import boto3
from pathlib import Path


class TestS3TransferWrapper(unittest.TestCase):
    def test_constructor(self):
        fileloader = FileLoader()
        config_path = Path(__file__).resolve().parent.joinpath("../data/fzfaws.yml")
        fileloader.load_config_file(config_path=str(config_path))
        transfer = S3TransferWrapper(boto3.client("s3"))
        self.assertEqual(transfer.s3transfer._manager.config.num_download_attempts, 6)
        self.assertEqual(transfer.transfer_config.num_download_attempts, 6)
