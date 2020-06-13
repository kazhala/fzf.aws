import io
import sys
import os
import unittest
from unittest.mock import PropertyMock, patch
from fzfaws.s3.upload_s3 import upload_s3
from fzfaws.s3 import S3
from fzfaws.utils import Pyfzf
from fzfaws.s3.helper.s3args import S3Args


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

    @patch.object(S3Args, "set_extra_args")
    @patch("fzfaws.s3.upload_s3.get_confirmation")
    @patch("fzfaws.s3.upload_s3.os.walk")
    @patch.object(Pyfzf, "get_local_file")
    def test_recusive_upload(
        self, mocked_local_file, mocked_walk, mocked_confirm, mocked_args
    ):
        curr_dirname = os.path.dirname(os.path.abspath(__file__))
        mocked_local_file.return_value = curr_dirname
        mocked_walk.return_value = [(curr_dirname, "/tmp", [__file__])]
        mocked_confirm.return_value = False

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        upload_s3(recursive=True, bucket="kazhala-file-lol/hello/")
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) upload: test_upload.py to s3://kazhala-file-lol/hello/test_upload.py\n",
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        upload_s3(recursive=True, bucket="kazhala-file-lol/hello/", exclude=["*"])
        self.assertEqual(
            self.capturedOutput.getvalue(), "",
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        upload_s3(
            recursive=True,
            bucket="kazhala-file-lol/hello/",
            exclude=["*"],
            include=["test_upload.py"],
            extra_config=True,
        )
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) upload: test_upload.py to s3://kazhala-file-lol/hello/test_upload.py\n",
        )
        mocked_args.assert_called_once()
