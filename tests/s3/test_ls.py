from fzfaws.s3.s3 import S3
import io
import sys
import unittest
from unittest.mock import ANY, PropertyMock, patch
from fzfaws.s3.ls_s3 import ls_s3, get_detailed_info
import boto3
from fzfaws.utils import BaseSession
from botocore.stub import Stubber


class TestS3LS(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    @patch("fzfaws.s3.ls_s3.get_detailed_info")
    @patch.object(S3, "set_s3_bucket")
    def test_bucket(self, mocked_bucket, mocked_info, mocked_client):
        ls_s3(bucket=True)
        mocked_info.assert_called_with(ANY, True, False, [])

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        s3 = boto3.client("s3")
        stubber = Stubber(s3)
        stubber.add_response("get_bucket_location", {"LocationConstraint": "us-east-1"})
        stubber.activate()
        mocked_client.return_value = s3
        ls_s3(bucket=True, url=True, bucketpath="kazhala-lol/")
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "https://s3-us-east-1.amazonaws.com/kazhala-lol/\n",
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ls_s3(bucket=True, uri=True, bucketpath="kazhala-lol/")
        self.assertEqual(
            self.capturedOutput.getvalue(), "s3://kazhala-lol/\n",
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ls_s3(bucket=True, name=True, bucketpath="kazhala-lol/")
        self.assertEqual(
            self.capturedOutput.getvalue(), "kazhala-lol\n",
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ls_s3(bucket=True, arn=True, bucketpath="kazhala-lol/")
        self.assertEqual(
            self.capturedOutput.getvalue(), "arn:aws:s3:::kazhala-lol/\n",
        )

    @patch.object(S3, "get_object_url")
    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    @patch("fzfaws.s3.ls_s3.get_detailed_info")
    @patch.object(S3, "get_object_version")
    @patch.object(S3, "set_s3_object")
    @patch.object(S3, "set_s3_bucket")
    def test_version(
        self,
        mocked_bucket,
        mocked_object,
        mocked_version,
        mocked_detail,
        mocked_client,
        mocked_url,
    ):
        mocked_version.return_value = [{"Key": "hello.txt", "VersionId": "111111"}]
        ls_s3(version=True)
        mocked_detail.assert_called_with(
            ANY, False, True, [{"Key": "hello.txt", "VersionId": "111111"}]
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ls_s3(version=True, versionid=True, bucketpath="kazhala-lol/hello.txt")
        self.assertEqual(self.capturedOutput.getvalue(), "111111\n")

        mocked_url.return_value = "https:hello"
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ls_s3(version=True, url=True, bucketpath="kazhala-lol/hello.txt")
        self.assertEqual(self.capturedOutput.getvalue(), "https:hello\n")
        mocked_url.assert_called_with(version="111111", object_key="hello.txt")

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ls_s3(version=True, uri=True, bucketpath="kazhala-lol/hello.txt")
        self.assertEqual(self.capturedOutput.getvalue(), "s3://kazhala-lol/hello.txt\n")

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ls_s3(version=True, name=True, bucketpath="kazhala-lol/hello.txt")
        self.assertEqual(self.capturedOutput.getvalue(), "kazhala-lol/hello.txt\n")

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ls_s3(version=True, arn=True, bucketpath="kazhala-lol/hello.txt")
        self.assertEqual(
            self.capturedOutput.getvalue(), "arn:aws:s3:::kazhala-lol/hello.txt\n"
        )

    @patch.object(S3, "get_object_url")
    @patch("fzfaws.s3.ls_s3.get_detailed_info")
    @patch.object(S3, "set_s3_object")
    @patch.object(S3, "set_s3_bucket")
    def test_normal(self, mocked_bucket, mocked_object, mocked_detail, mocked_url):
        ls_s3()
        mocked_detail.assert_called_with(ANY, False, False, [])

        mocked_url.return_value = "https:hello"
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ls_s3(url=True, bucketpath="kazhala-lol/hello.txt")
        self.assertEqual(self.capturedOutput.getvalue(), "https:hello\n")
        mocked_url.assert_called_with(object_key="hello.txt")

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ls_s3(uri=True, bucketpath="kazhala-lol/hello.txt")
        self.assertEqual(self.capturedOutput.getvalue(), "s3://kazhala-lol/hello.txt\n")

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ls_s3(name=True, bucketpath="kazhala-lol/hello.txt")
        self.assertEqual(self.capturedOutput.getvalue(), "kazhala-lol/hello.txt\n")

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ls_s3(arn=True, bucketpath="kazhala-lol/hello.txt")
        self.assertEqual(
            self.capturedOutput.getvalue(), "arn:aws:s3:::kazhala-lol/hello.txt\n"
        )
