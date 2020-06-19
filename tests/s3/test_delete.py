import io
import json
import os
import sys
import unittest
from unittest.mock import patch, PropertyMock, ANY

import boto3
from botocore.paginate import Paginator
from botocore.stub import Stubber

from fzfaws.s3.delete_s3 import delete_s3, find_all_version_files
from fzfaws.s3.s3 import S3
from fzfaws.utils.session import BaseSession


class TestS3Delete(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch.object(Paginator, "paginate")
    def test_find_all_version_files(self, mocked_result):
        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/s3_object_ver.json"
        )
        with open(data_path, "r") as file:
            mocked_result.return_value = json.load(file)

        s3 = boto3.client("s3")
        result = find_all_version_files(s3, "kazhala-lol", "")
        self.assertEqual(
            result,
            [
                " elb.pem",
                " w tf.txt",
                " wtf.txt",
                "../",
                ".DS_Store",
                "CHANGELOG.md",
                "README.md",
                "wtf.pem",
            ],
        )

        result = find_all_version_files(
            s3, "kazhala-lol", "", exclude=["*.pem"], include=["wtf.pem"]
        )
        self.assertEqual(
            result,
            [
                " w tf.txt",
                " wtf.txt",
                "../",
                ".DS_Store",
                "CHANGELOG.md",
                "README.md",
                "wtf.pem",
            ],
        )

        result = find_all_version_files(s3, "kazhala-lol", "", deletemark=True)
        self.assertEqual(
            result, [" elb.pem", " w tf.txt", " wtf.txt", ".DS_Store"],
        )

    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    @patch("fzfaws.s3.delete_s3.get_confirmation")
    @patch("fzfaws.s3.delete_s3.walk_s3_folder")
    @patch("fzfaws.s3.delete_s3.find_all_version_files")
    @patch.object(S3, "get_object_version")
    @patch.object(S3, "set_s3_path")
    @patch.object(S3, "set_s3_bucket")
    def test_delete_object_recursive(
        self,
        mocked_bucket,
        mocked_path,
        mocked_version,
        mocked_find,
        mocked_walk,
        mocked_confirm,
        mocked_client,
    ):
        # test params
        mocked_confirm.return_value = False
        delete_s3(recursive=True)
        mocked_bucket.assert_called_once()
        mocked_path.assert_called_once()
        mocked_walk.assert_called_once()

        # test allversion
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        mocked_confirm.return_value = True
        s3 = boto3.client("s3")
        stubber = Stubber(s3)
        stubber.add_response(
            "delete_object",
            {
                "DeleteMarker": False,
                "VersionId": "string",
                "RequestCharged": "requester",
            },
            expected_params={
                "Bucket": "kazhala-lol",
                "Key": "wtf.pem",
                "VersionId": "111111",
            },
        )
        stubber.activate()
        mocked_client.return_value = s3
        mocked_find.return_value = ["wtf.pem"]
        mocked_version.return_value = [{"Key": "wtf.pem", "VersionId": "111111"}]
        delete_s3(bucket="kazhala-lol/", recursive=True, allversion=True, clean=True)
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) delete: s3://kazhala-lol/wtf.pem and all non-current versions\ndelete: s3://kazhala-lol/wtf.pem with version 111111\n",
        )
        mocked_version.assert_called_once_with(
            key="wtf.pem", delete=True, select_all=True, non_current=True
        )
        mocked_find.assert_called_with(ANY, "kazhala-lol", "", [], [], [], False)

        # test recursive non version delete
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        mocked_confirm.return_value = True
        s3 = boto3.client("s3")
        stubber = Stubber(s3)
        stubber.add_response(
            "delete_object",
            {
                "DeleteMarker": False,
                "VersionId": "string",
                "RequestCharged": "requester",
            },
            expected_params={"Bucket": "kazhala-lol", "Key": "wtf.pem",},
        )
        stubber.activate()
        mocked_client.return_value = s3
        mocked_walk.return_value = [("wtf.pem", "wtf.pem")]
        mocked_version.return_value = [{"Key": "wtf.pem", "VersionId": "111111"}]
        delete_s3(bucket="kazhala-lol/", recursive=True)
        self.assertEqual(
            self.capturedOutput.getvalue(), "delete: s3://kazhala-lol/wtf.pem\n",
        )
        mocked_walk.assert_called_with(ANY, "kazhala-lol", "", "", [], [], [], "delete")

    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    @patch("fzfaws.s3.delete_s3.get_confirmation")
    @patch.object(S3, "get_object_version")
    @patch.object(S3, "set_s3_object")
    @patch.object(S3, "set_s3_bucket")
    def test_delete_object_version(
        self,
        mocked_bucket,
        mocked_object,
        mocked_version,
        mocked_confirm,
        mocked_client,
    ):
        mocked_confirm.return_value = True
        # param test
        delete_s3(version=True, allversion=True, mfa="111111 111111", deletemark=True)
        mocked_bucket.assert_called_once()
        mocked_object.assert_called_once_with(
            version=True, multi_select=False, deletemark=True
        )
        mocked_version.assert_called_once_with(
            delete=True, select_all=False, multi_select=False
        )

        # version test
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        s3 = boto3.client("s3")
        stubber = Stubber(s3)
        stubber.add_response(
            "delete_object",
            {
                "DeleteMarker": False,
                "VersionId": "string",
                "RequestCharged": "requester",
            },
            expected_params={
                "Bucket": "kazhala-lol",
                "Key": "wtf.pem",
                "MFA": "",
                "VersionId": "111111",
            },
        )
        stubber.activate()
        mocked_client.return_value = s3
        mocked_version.return_value = [{"Key": "wtf.pem", "VersionId": "111111"}]
        delete_s3(version=True, bucket="kazhala-lol/")
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) delete: s3://kazhala-lol/wtf.pem with version 111111\ndelete: s3://kazhala-lol/wtf.pem with version 111111\n",
        )
        mocked_version.assert_called_with(
            delete=True, select_all=False, multi_select=True
        )
        mocked_object.assert_called_with(
            version=True, multi_select=True, deletemark=False
        )

        # mfa
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        s3 = boto3.client("s3")
        stubber = Stubber(s3)
        stubber.add_response(
            "delete_object",
            {
                "DeleteMarker": False,
                "VersionId": "string",
                "RequestCharged": "requester",
            },
            expected_params={
                "Bucket": "kazhala-lol",
                "Key": "wtf.pem",
                "MFA": "99999 111111",
                "VersionId": "111111",
            },
        )
        stubber.activate()
        mocked_client.return_value = s3
        mocked_version.return_value = [{"Key": "wtf.pem", "VersionId": "111111"}]
        delete_s3(
            version=True,
            bucket="kazhala-lol/",
            mfa="99999 111111",
            allversion=True,
            recursive=True,
        )
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) delete: s3://kazhala-lol/wtf.pem with version 111111\ndelete: s3://kazhala-lol/wtf.pem with version 111111\n",
        )
        mocked_version.assert_called_with(
            delete=True, select_all=False, multi_select=False
        )
        mocked_object.assert_called_with(
            version=True, multi_select=False, deletemark=False
        )

    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    @patch("fzfaws.s3.delete_s3.get_confirmation")
    @patch.object(S3, "set_s3_object")
    @patch.object(S3, "set_s3_bucket")
    def test_delete_object_single(
        self, mocked_bucket, mocked_object, mocked_confirm, mocked_client
    ):
        # param test
        delete_s3()
        mocked_bucket.assert_called_once()
        mocked_object.assert_called_once_with(
            version=False, multi_select=True, deletemark=False
        )

        # single deletion test
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        s3 = boto3.client("s3")
        stubber = Stubber(s3)
        stubber.add_response(
            "delete_object",
            {
                "DeleteMarker": False,
                "VersionId": "string",
                "RequestCharged": "requester",
            },
            expected_params={"Bucket": "kazhala-lol", "Key": "wtf.pem",},
        )
        stubber.activate()
        mocked_client.return_value = s3
        delete_s3(bucket="kazhala-lol/wtf.pem")
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) delete: s3://kazhala-lol/wtf.pem\ndelete: s3://kazhala-lol/wtf.pem\n",
        )
        mocked_object.assert_called_with(
            version=False, multi_select=True, deletemark=False
        )
