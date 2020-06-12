import io
import sys
import unittest
from unittest.mock import patch
from fzfaws.s3.helper.sync_s3 import sync_s3
import subprocess


class TestS3Sync(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch("fzfaws.s3.helper.sync_s3.get_confirmation")
    @patch.object(subprocess, "Popen")
    def test_no_extra(self, mocked_popen, mocked_confirmation):
        mocked_confirmation.return_value = True
        attrs = {"communicate.return_value": ("output", "error")}
        mocked_popen.configure_mock(**attrs)
        sync_s3(from_path="hello/world", to_path="s3://hello")
        mocked_popen.assert_called_with(
            ["aws", "s3", "sync", "hello/world", "s3://hello",]
        )

    @patch("fzfaws.s3.helper.sync_s3.get_confirmation")
    @patch.object(subprocess, "Popen")
    def test_extra(self, mocked_popen, mocked_confirmation):
        mocked_confirmation.return_value = True
        attrs = {"communicate.return_value": ("output", "error")}
        mocked_popen.configure_mock(**attrs)
        sync_s3(["lol"], ["foo", "boo"], "tmp", "s3://yes")
        mocked_popen.assert_called_with(
            [
                "aws",
                "s3",
                "sync",
                "tmp",
                "s3://yes",
                "--exclude",
                "lol",
                "--include",
                "foo",
                "boo",
            ]
        )

        sync_s3(["lol"], [], "tmp", "s3://yes")
        mocked_popen.assert_called_with(
            ["aws", "s3", "sync", "tmp", "s3://yes", "--exclude", "lol",]
        )
