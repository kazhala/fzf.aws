import sys
import io
import unittest
from unittest.mock import patch
from fzfaws.s3.helper.s3progress import S3Progress
import boto3
from botocore.stub import Stubber


class TestS3Progress(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch("os.path.getsize")
    def test_constructor(self, mocked_size):
        mocked_size.return_value = 10

        client = boto3.client("s3")
        stubber = Stubber(client)
        stubber.add_response("head_object", {"ContentLength": 100})
        stubber.activate()

        progress = S3Progress(filename=__file__)
        self.assertEqual(progress._filename, __file__)
        self.assertEqual(progress._seen_so_far, 0)
        self.assertEqual(progress._size, 10)

        progress = S3Progress(filename=__file__, client=client, bucket="hello")
        self.assertEqual(progress._filename, __file__)
        self.assertEqual(progress._seen_so_far, 0)
        self.assertEqual(progress._size, 100)

    @patch("os.path.getsize")
    def test_call(self, mocked_size):
        mocked_size.return_value = 1000
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        progress = S3Progress(filename=__file__)
        progress(bytes_amount=20)
        self.assertRegex(
            self.capturedOutput.getvalue(), r"test_s3progress.py  20 Bytes / 1000 Bytes"
        )

    def test_human_readable_size(self):
        progress = S3Progress(filename=__file__)
        result = progress.human_readable_size(1000)
        self.assertEqual(result, "1000 Bytes")
        result = progress.human_readable_size(1024)
        self.assertEqual(result, "1.0 KiB")
        result = progress.human_readable_size(1048576)
        self.assertEqual(result, "1.0 MiB")
        result = progress.human_readable_size(1073741824)
        self.assertEqual(result, "1.0 GiB")
        result = progress.human_readable_size(10737418991)
        self.assertEqual(result, "10.0 GiB")
