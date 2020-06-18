import json
import io
import sys
import os
import unittest
from unittest.mock import patch
from fzfaws.s3.delete_s3 import delete_s3, find_all_version_files
from botocore.paginate import Paginator
import boto3


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
