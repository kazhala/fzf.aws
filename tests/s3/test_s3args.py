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

        # normal no version test
        s3 = boto3.resource("s3")
        stubber = Stubber(s3.meta.client)
        stubber.add_response("get_object", response)
        stubber.activate()
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
        mocked_execute.assert_called_with(
            print_col=1,
            multi_select=True,
            empty_allow=False,
            header="Select attributes to configure",
        )

        # normal no call no version test
        mocked_encryption.reset_mock()
        mocked_execute.reset_mock()
        mocked_tags.reset_mock()
        mocked_append.reset_mock()
        mocked_tags.reset_mock()
        mocked_metadata.reset_mock()
        mocked_storage.reset_mock()
        mocked_acl.reset_mock()
        s3 = boto3.resource("s3")
        stubber = Stubber(s3.meta.client)
        stubber.add_response("get_object", response)
        stubber.activate()
        self.s3_args.set_extra_args(storage=True, upload=True)
        mocked_storage.assert_called()
        mocked_append.assert_not_called()
        mocked_execute.assert_not_called()
        mocked_tags.assert_not_called()
        mocked_append.assert_not_called()
        mocked_tags.assert_not_called()
        mocked_metadata.assert_not_called()
        mocked_acl.assert_not_called()
        mocked_encryption.assert_not_called()

        # version test
        mocked_encryption.reset_mock()
        mocked_execute.reset_mock()
        mocked_tags.reset_mock()
        mocked_append.reset_mock()
        mocked_tags.reset_mock()
        mocked_metadata.reset_mock()
        mocked_storage.reset_mock()
        mocked_acl.reset_mock()
        s3 = boto3.resource("s3")
        stubber = Stubber(s3.meta.client)
        stubber.add_response("get_object", response)
        stubber.activate()
        mocked_execute.return_value = ["ACL", "Tagging"]
        self.s3_args.set_extra_args(
            version=[{"Key": "hello.json", "VersionId": "11111111"}]
        )
        mocked_append.assert_called_with("Tagging")
        mocked_execute.assert_called_with(
            print_col=1,
            multi_select=True,
            empty_allow=False,
            header="Select attributes to configure",
        )
        mocked_storage.assert_not_called()
        mocked_acl.assert_called_with(
            original=True, version=[{"Key": "hello.json", "VersionId": "11111111"}]
        )
        mocked_encryption.assert_not_called()
        mocked_metadata.assert_not_called()
        mocked_tags.assert_called_with(
            original=True, version=[{"Key": "hello.json", "VersionId": "11111111"}]
        )

    @patch("builtins.input")
    def test_set_metadata(self, mocked_input):
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        self.s3_args._extra_args = {}
        mocked_input.return_value = "foo=boo"
        self.s3_args.set_metadata(original="hello")
        self.assertEqual(self.s3_args._extra_args, {"Metadata": {"foo": "boo"}})
        self.assertRegex(self.capturedOutput.getvalue(), "Orignal: hello")

        mocked_input.return_value = "foo=boo&hello=world&"
        self.s3_args.set_metadata()
        self.assertEqual(
            self.s3_args._extra_args, {"Metadata": {"foo": "boo", "hello": "world"}}
        )

    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Pyfzf, "append_fzf")
    def test_set_storageclass(self, mocked_append, mocked_execute):
        self.s3_args._extra_args = {}
        mocked_execute.return_value = "STANDARD"
        self.s3_args.set_storageclass(original="GLACIER")
        mocked_append.assert_called_with("DEEP_ARCHIVE\n")
        mocked_execute.assert_called_with(
            empty_allow=True,
            print_col=1,
            header="Select a storage class, esc to use the default storage class of the bucket setting\nOriginal: GLACIER",
        )
        self.assertEqual(self.s3_args._extra_args, {"StorageClass": "STANDARD"})

        mocked_execute.return_value = "REDUCED_REDUNDANCY"
        self.s3_args.set_storageclass()
        mocked_append.assert_called_with("DEEP_ARCHIVE\n")
        mocked_execute.assert_called_with(
            empty_allow=True,
            print_col=1,
            header="Select a storage class, esc to use the default storage class of the bucket setting",
        )
        self.assertEqual(
            self.s3_args._extra_args, {"StorageClass": "REDUCED_REDUNDANCY"}
        )
