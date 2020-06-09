from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.session import BaseSession
import io
import json
import os
import sys
import unittest
from unittest.mock import PropertyMock, patch
from fzfaws.s3.helper.s3args import S3Args
from fzfaws.s3 import S3
import boto3
from botocore.stub import Stubber


class TestS3Args(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput
        s3 = S3()
        s3.bucket_name = "hello"
        s3.path_list = ["hello.json"]
        self.s3_args = S3Args(s3)

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_constructor(self):
        self.assertIsInstance(self.s3_args.s3, S3)
        self.assertEqual(self.s3_args._extra_args, {})

    @patch.object(S3Args, "set_tags")
    @patch.object(S3Args, "set_metadata")
    @patch.object(S3Args, "set_encryption")
    @patch.object(S3Args, "set_ACL")
    @patch.object(S3Args, "set_storageclass")
    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Pyfzf, "append_fzf")
    @patch.object(BaseSession, "resource", new_callable=PropertyMock)
    def test_set_extra_args(
        self,
        mocked_resource,
        mocked_append,
        mocked_execute,
        mocked_storage,
        mocked_acl,
        mocked_encryption,
        mocked_metadata,
        mocked_tags,
    ):
        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/s3_obj.json"
        )
        with open(data_path, "r") as file:
            response = json.load(file)
        s3 = boto3.resource("s3")
        stubber = Stubber(s3.meta.client)
        stubber.add_response("get_object", response)
        stubber.activate()

        # normal no version test
        mocked_execute.return_value = [
            "StorageClass",
            "ACL",
            "Metadata",
            "Encryption",
            "Tagging",
        ]
        self.s3_args.set_extra_args()
        mocked_append.assert_called_with("Tagging\n")
        mocked_storage.assert_called()
        mocked_acl.assert_called_with(original=True, version=[])
        mocked_encryption.assert_called()
        mocked_metadata.assert_called()
        mocked_tags.assert_called_with(original=True, version=[])
