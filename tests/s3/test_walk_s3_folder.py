import io
import json
import os
import sys
import unittest
from unittest.mock import patch
from botocore.paginate import Paginator
from fzfaws.s3.helper.walk_s3_folder import walk_s3_folder
import boto3


class TestS3WalkFolder(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch("fzfaws.s3.helper.walk_s3_folder.exclude_file")
    @patch.object(Paginator, "paginate")
    def test_walk(self, mocked_paginator, mocked_exclude):
        data_path2 = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/s3_object_nested.json"
        )
        with open(data_path2, "r") as file:
            response = json.load(file)

        mocked_paginator.return_value = response
        mocked_exclude.return_value = False
        client = boto3.client("s3")
        result = walk_s3_folder(
            client, "kazhala-file-transfer", "wtf/hello", "", destination_path="tmp"
        )
        self.assertEqual(result, [("wtf/hello/hello.txt", "tmp/wtf/hello/hello.txt")])
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) download: s3://kazhala-file-transfer/wtf/hello/hello.txt to tmp/wtf/hello/hello.txt\n",
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        result = walk_s3_folder(
            client,
            "kazhala-file-transfer",
            "wtf/hello/",
            "wtf/hello/",
            [],
            [],
            [],
            "download",
            "/Users/kazhala/tmp",
        )
        self.assertEqual(
            result, [("wtf/hello/hello.txt", "/Users/kazhala/tmp/hello.txt")]
        )
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) download: s3://kazhala-file-transfer/wtf/hello/hello.txt to /Users/kazhala/tmp/hello.txt\n",
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        result = walk_s3_folder(
            client,
            "kazhala-file-transfer",
            "wtf/hello/",
            "",
            operation="delete",
            destination_path="/",
        )
        self.assertEqual(result, [("wtf/hello/hello.txt", "/wtf/hello/hello.txt")])
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) delete: s3://kazhala-file-transfer/wtf/hello/hello.txt\n",
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        result = walk_s3_folder(
            client,
            "kazhala-file-transfer",
            "wtf/hello/",
            "",
            operation="bucket",
            destination_path="",
            destination_bucket="kazhala-file-transfer2",
        )
        self.assertEqual(result, [("wtf/hello/hello.txt", "wtf/hello/hello.txt")])
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) copy: s3://kazhala-file-transfer/wtf/hello/hello.txt to s3://kazhala-file-transfer2/wtf/hello/hello.txt\n",
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        result = walk_s3_folder(
            client,
            "kazhala-file-transfer",
            "wtf/hello/",
            "",
            operation="object",
            destination_path="",
        )
        self.assertEqual(result, [("wtf/hello/hello.txt", "wtf/hello/hello.txt")])
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) update: s3://kazhala-file-transfer/wtf/hello/hello.txt\n",
        )

        mocked_exclude.return_value = True
        result = walk_s3_folder(client, "kazhala-file-transfer", "", "")
        self.assertEqual(result, [])
