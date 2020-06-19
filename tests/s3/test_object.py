from fzfaws.s3.helper.s3args import S3Args
from botocore.stub import Stubber
from fzfaws.utils.session import BaseSession
import io
import sys
import unittest
from unittest.mock import PropertyMock, patch, ANY
from fzfaws.s3.object_s3 import object_s3
from fzfaws.s3 import S3
import boto3


class TestS3Object(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    @patch("fzfaws.s3.object_s3.get_copy_args")
    @patch("boto3.s3.inject.copy")
    @patch.object(S3, "get_object_version")
    @patch("builtins.input")
    @patch("fzfaws.s3.object_s3.get_confirmation")
    @patch.object(S3, "set_s3_object")
    @patch.object(S3, "set_s3_bucket")
    def test_name(
        self,
        mocked_bucket,
        mocked_object,
        mocked_confirm,
        mocked_input,
        mocked_version,
        mocked_copy,
        mocked_args,
        mocked_client,
    ):
        mocked_confirm.return_value = False
        mocked_input.return_value = "yes.txt"
        mocked_version.return_value = [{"Key": "hello.txt", "VersionId": "111111"}]

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        object_s3(name=True)
        mocked_bucket.assert_called_once()
        mocked_object.assert_called_once_with(False)
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "Enter the new name below (format: newname or path/newname for a new path)\n(dryrun) rename: s3:/// to s3:///yes.txt\n",
        )

        mocked_confirm.return_value = True
        mocked_copy.return_value = True
        mocked_args.return_value = {}
        s3 = boto3.client("s3")
        stubber = Stubber(s3)
        stubber.add_response("head_object", {"ContentLength": 100})
        stubber.activate()
        mocked_client.return_value = s3

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        mocked_bucket.reset_mock()
        mocked_object.reset_mock()
        object_s3(name=True, version=True, bucket="kazhala-lol/hello.txt")
        mocked_bucket.assert_not_called()
        mocked_object.assert_not_called()
        mocked_version.assert_called_with(key="hello.txt")
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "Enter the new name below (format: newname or path/newname for a new path)\n(dryrun) rename: s3://kazhala-lol/hello.txt to s3://kazhala-lol/yes.txt with version 111111\nrename: s3://kazhala-lol/hello.txt to s3://kazhala-lol/yes.txt with version 111111\n",
        )
        mocked_copy.assert_called_with(
            {"Bucket": "kazhala-lol", "Key": "hello.txt", "VersionId": "111111"},
            "kazhala-lol",
            "yes.txt",
            Callback=ANY,
            Config=ANY,
            ExtraArgs={},
        )

    @patch("fzfaws.s3.object_s3.get_confirmation")
    @patch("fzfaws.s3.object_s3.walk_s3_folder")
    @patch.object(S3Args, "set_extra_args")
    @patch.object(S3, "set_s3_path")
    @patch.object(S3, "set_s3_bucket")
    def test_recursive(
        self, mocked_bucket, mocked_path, mocked_args, mocked_walk, mocked_confirm,
    ):
        mocked_confirm.return_value = False
        mocked_walk.return_value = [("hello.txt", "hello.txt")]

        object_s3(recursive=True)
        mocked_bucket.assert_called_once()
        mocked_path.assert_called_once()
        mocked_args.assert_called_once_with(False, False, False, False, False)
        mocked_walk.assert_called_with(ANY, "", "", "", [], [], [], "object", "", "")

        mocked_bucket.reset_mock()
        mocked_path.reset_mock()
        mocked_args.reset_mock()
        object_s3(recursive=True, bucket="kazhala-lol/hello/")
        mocked_bucket.assert_not_called()
        mocked_path.assert_not_called()
        mocked_args.assert_called_once_with(False, False, False, False, False)
        mocked_walk.assert_called_with(
            ANY,
            "kazhala-lol",
            "hello/",
            "hello/",
            [],
            [],
            [],
            "object",
            "hello/",
            "kazhala-lol",
        )

    @patch("fzfaws.s3.object_s3.get_confirmation")
    @patch.object(S3Args, "set_extra_args")
    @patch.object(S3, "get_object_version")
    @patch.object(S3, "set_s3_object")
    @patch.object(S3, "set_s3_bucket")
    def test_version(
        self, mocked_bucket, mocked_object, mocked_version, mocked_args, mocked_confirm
    ):
        mocked_confirm.return_value = False
        mocked_version.return_value = [{"Key": "hello.txt", "VersionId": "111111"}]

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        object_s3(version=True, allversion=True)
        mocked_bucket.assert_called_once()
        mocked_object.assert_called_once()
        mocked_version.assert_called_once_with(select_all=True)
        mocked_args.assert_called_once_with(
            False, False, version=[{"Key": "hello.txt", "VersionId": "111111"}]
        )
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) update: s3:///hello.txt with version 111111\n",
        )

        mocked_bucket.reset_mock()
        mocked_object.reset_mock()
        mocked_version.reset_mock()
        mocked_args.reset_mock()
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        object_s3(version=True, bucket="kazhala-lol/hello.txt")
        mocked_bucket.assert_not_called()
        mocked_object.assert_not_called()
        mocked_version.assert_called_once_with(select_all=False)
        mocked_args.assert_called_once_with(
            False, False, version=[{"Key": "hello.txt", "VersionId": "111111"}]
        )
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) update: s3://kazhala-lol/hello.txt with version 111111\n",
        )

    @patch("fzfaws.s3.object_s3.get_confirmation")
    @patch.object(S3Args, "set_extra_args")
    @patch.object(S3, "set_s3_object")
    @patch.object(S3, "set_s3_bucket")
    def test_singel(self, mocked_bucket, mocked_object, mocked_args, mocked_confirm):
        mocked_confirm.return_value = False
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        object_s3()
        mocked_bucket.assert_called_once()
        mocked_object.assert_called_once()
        mocked_args.assert_called_once_with(False, False, False, False, False)
        self.assertEqual(self.capturedOutput.getvalue(), "(dryrun) update: s3:///\n")

        mocked_bucket.reset_mock()
        mocked_args.reset_mock()
        mocked_object.reset_mock()
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        object_s3(bucket="kazhala-lol/hello.txt")
        mocked_bucket.assert_not_called()
        mocked_object.assert_not_called()
        mocked_args.assert_called_once_with(False, False, False, False, False)
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) update: s3://kazhala-lol/hello.txt\n",
        )
