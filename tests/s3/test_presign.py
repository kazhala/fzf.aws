import io
import sys
import unittest
from unittest.mock import patch

from fzfaws.s3.presign_s3 import presign_s3
from fzfaws.s3.s3 import S3


class TestS3Presign(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch("botocore.signers.generate_presigned_url")
    @patch.object(S3, "get_object_version")
    @patch.object(S3, "set_s3_object")
    @patch.object(S3, "set_s3_bucket")
    def test_version(self, mocked_bucket, mocked_object, mocked_version, mocked_signer):
        presign_s3(version=True)
        mocked_bucket.assert_called_once()
        mocked_object.assert_called_once_with(version=True, multi_select=True)
        mocked_version.assert_called_once()
        mocked_signer.assert_not_called()

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        mocked_bucket.reset_mock()
        mocked_object.reset_mock()
        mocked_version.reset_mock()
        mocked_version.return_value = [{"Key": "hello.txt", "VersionId": "11111"}]
        mocked_signer.return_value = "https:hello.txt"
        presign_s3(version=True, bucket="kazhala-lol/hello.txt", expires_in=1)
        mocked_bucket.assert_not_called()
        mocked_object.assert_not_called()
        mocked_version.assert_called_once()
        mocked_signer.assert_called_with(
            "get_object",
            Params={"Bucket": "kazhala-lol", "Key": "hello.txt", "VersionId": "11111"},
            ExpiresIn=1,
        )
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "--------------------------------------------------------------------------------\nhello.txt:\nhttps:hello.txt\n",
        )

    @patch("botocore.signers.generate_presigned_url")
    @patch.object(S3, "set_s3_object")
    @patch.object(S3, "set_s3_bucket")
    def test_normal(self, mocked_bucket, mocked_object, mocked_signer):
        presign_s3()
        mocked_bucket.assert_called_once()
        mocked_object.assert_called_once_with(version=False, multi_select=True)

        mocked_signer.return_value = "https:hello.txt"
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        mocked_bucket.reset_mock()
        mocked_object.reset_mock()
        presign_s3(bucket="kazhala-lol/hello.txt")
        mocked_bucket.assert_not_called()
        mocked_object.assert_not_called()
        mocked_signer.assert_called_with(
            "get_object",
            Params={"Bucket": "kazhala-lol", "Key": "hello.txt"},
            ExpiresIn=3600,
        )
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "--------------------------------------------------------------------------------\nhello.txt:\nhttps:hello.txt\n",
        )
