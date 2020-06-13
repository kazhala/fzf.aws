import io
import sys
import os
import unittest
from unittest.mock import patch
from fzfaws.s3.upload_s3 import upload_s3
from fzfaws.s3 import S3
from fzfaws.utils import Pyfzf


class TestS3Upload(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch.object(S3, "set_s3_path")
    @patch.object(S3, "set_s3_bucket")
    @patch("fzfaws.s3.upload_s3.sync_s3")
    @patch.object(Pyfzf, "get_local_file")
    def test_sync(self, mocked_local_file, mocked_sync, mocked_bucket, mocked_path):
        mocked_local_file.return_value = "/tmp"
        upload_s3(sync=True, bucket="kazhala-file-transfer/hello/")
        mocked_sync.assert_called_with(
            exclude=[],
            include=[],
            from_path="/tmp",
            to_path="s3://kazhala-file-transfer/hello/",
        )
        mocked_local_file.assert_called_with(
            search_from_root=False,
            directory=True,
            hidden=False,
            empty_allow=True,
            multi_select=False,
        )

        upload_s3(sync=True, search_root=True, recursive=True, hidden=True)
        mocked_sync.assert_called_with(
            exclude=[], include=[], from_path="/tmp", to_path="s3:///",
        )
        mocked_local_file.assert_called_with(
            search_from_root=True,
            directory=True,
            hidden=True,
            empty_allow=True,
            multi_select=False,
        )
        mocked_bucket.assert_called_once()
        mocked_path.assert_called_once()
