from fzfaws.utils.pyfzf import Pyfzf
import os
import io
import sys
import unittest
from unittest.mock import patch
from fzfaws.s3.download_s3 import download_s3
from fzfaws.s3 import S3


class TestS3Download(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch("fzfaws.s3.download_s3.sync_s3")
    @patch.object(Pyfzf, "get_local_file")
    @patch.object(S3, "set_s3_path")
    def test_sync(self, mocked_path, mocked_local, mocked_sync):
        mocked_local.return_value = os.path.dirname(__file__)
        download_s3(sync=True, bucket="kazhala-lol/hello/")
        mocked_sync.assert_called_with(
            exclude=[],
            include=[],
            from_path="s3://kazhala-lol/hello/",
            to_path=os.path.dirname(__file__),
        )
        mocked_local.assert_called_with(False, directory=True, hidden=False)

        download_s3(sync=True, bucket="kazhala-lol/")
        mocked_path.assert_called_with(download=True)
        mocked_sync.assert_called_with(
            exclude=[],
            include=[],
            from_path="s3://kazhala-lol/",
            to_path=os.path.dirname(__file__),
        )

        mocked_local.reset_mock()
        download_s3(
            sync=True, bucket="kazhala-lol/hello/", hidden=True, search_from_root=True
        )
        mocked_sync.assert_called_with(
            exclude=[],
            include=[],
            from_path="s3://kazhala-lol/hello/",
            to_path=os.path.dirname(__file__),
        )
        mocked_local.assert_called_with(True, directory=True, hidden=True)

    @patch("fzfaws.s3.download_s3.get_confirmation")
    @patch("fzfaws.s3.download_s3.walk_s3_folder")
    def test_recursive(self, mocked_walk, mocked_confirm):
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        mocked_walk.return_value = [("hello/hello.txt", "hello.txt")]
        mocked_walk.side_effect = lambda a, b, c, d, e, g, h, i, j: print(
            b, c, d, e, g, h, i, j
        )
        mocked_confirm.return_value = False
        download_s3(recursive=True, bucket="kazhala-lol/hello/", local_path="/tmp")
        mocked_walk.assert_called()
        mocked_confirm.assert_called()
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "kazhala-lol hello/ hello/ [] [] [] download /tmp\n",
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        mocked_confirm.return_value = False
        download_s3(
            recursive=True,
            bucket="kazhala-lol/yes/",
            local_path="/usr",
            exclude=["*"],
            include=["*.git"],
        )
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "kazhala-lol yes/ yes/ [] ['*'] ['*.git'] download /usr\n",
        )

    @patch("fzfaws.s3.download_s3.get_confirmation")
    @patch.object(S3, "get_object_version")
    @patch.object(S3, "set_s3_object")
    def test_version(self, mocked_s3_object, mocked_version, mocked_confirm):
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        mocked_version.return_value = [
            {"Key": "hello/hello.txt", "VersionId": "11111111"}
        ]
        mocked_confirm.return_value = False
        download_s3(version=True, bucket="kazhala-lol/hello/", local_path="/tmp")
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) download: s3://kazhala-lol/hello/hello.txt to /tmp/hello.txt with version 11111111\n",
        )

        download_s3(version=True, bucket="kazhala-lol/", local_path="/tmp")
        mocked_s3_object.assert_called_with(multi_select=True, version=True)

    @patch.object(S3, "set_s3_object")
    @patch("fzfaws.s3.download_s3.get_confirmation")
    def test_single(self, mocked_confirm, mocked_object):
        mocked_confirm.return_value = False
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        download_s3(bucket="kazhala-lol/hello/hello.txt", local_path="/tmp")
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) download: s3://kazhala-lol/hello/hello.txt to /tmp/hello.txt\n",
        )
        mocked_object.assert_not_called()

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        download_s3(bucket="kazhala-lol/", local_path="/tmp")
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) download: s3://kazhala-lol/ to /tmp/\n",
        )
        mocked_object.assert_called_with(multi_select=True, version=False)
