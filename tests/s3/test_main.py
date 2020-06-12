import io
import sys
import unittest
from unittest.mock import patch
from fzfaws.s3.main import s3


class TestS3Main(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_help(self):
        self.assertRaises(SystemExit, s3, ["-h"])

    @patch("fzfaws.s3.main.upload_s3")
    def test_upload(self, mocked_upload):
        s3(["upload"])
        mocked_upload.assert_called_with(
            False, None, [], False, False, False, False, [], [], False
        )

        s3(["upload", "-P", "-b", "kazhala-file-transfer/", "-p", "hello.txt", "-E"])
        mocked_upload.assert_called_with(
            True,
            "kazhala-file-transfer/",
            ["hello.txt"],
            False,
            False,
            False,
            False,
            [],
            [],
            True,
        )

        s3(
            [
                "upload",
                "-P",
                "root",
                "-r",
                "-R",
                "-H",
                "-s",
                "-e",
                "*.git",
                "*.lol",
                "-i",
                "hello.txt",
            ]
        )
        mocked_upload.assert_called_with(
            "root",
            None,
            [],
            True,
            True,
            True,
            True,
            ["*.git", "*.lol"],
            ["hello.txt"],
            False,
        )

    @patch("fzfaws.s3.main.download_s3")
    def test_download(self, mocked_download):
        s3(["download"])
        mocked_download.assert_called_with(
            False, None, None, False, False, False, [], [], False, False
        )

        s3(["download", "-r", "-R", "-s", "-e", "lol", "-v", "-H"])
        mocked_download.assert_called_with(
            False, None, None, True, True, True, ["lol"], [], True, True
        )

        s3(["download", "-P", "root", "-b", "kazhala-file"])
        mocked_download.assert_called_with(
            "root", "kazhala-file", None, False, False, False, [], [], False, False
        )

    @patch("fzfaws.s3.main.bucket_s3")
    def test_bucket(self, mocked_bucket):
        s3(["bucket"])
        mocked_bucket.assert_called_with(
            False, None, None, False, False, [], [], False, False
        )

        s3(["bucket", "-b", "kazhala", "-t", "yes", "-r", "-s"])
        mocked_bucket.assert_called_with(
            False, "kazhala", "yes", True, True, [], [], False, False
        )

    @patch("fzfaws.s3.main.delete_s3")
    def test_delete(self, mocked_delete):
        s3(["delete"])
        mocked_delete.assert_called_with(
            False, None, False, [], [], "", False, False, False, False
        )

        s3(
            [
                "delete",
                "-P",
                "root",
                "-b",
                "kazhala",
                "-r",
                "-m",
                "111111",
                "010010",
                "-v",
                "-V",
                "--clean",
                "--deletemark",
            ]
        )
        mocked_delete.assert_called_with(
            "root", "kazhala", True, [], [], "111111 010010", True, True, True, True
        )

    @patch("fzfaws.s3.main.presign_s3")
    def test_presign(self, mocked_presign):
        s3(["presign"])
        mocked_presign.assert_called_with(False, None, False, 3600)

        s3(["presign", "-e", "111111", "-v"])
        mocked_presign.assert_called_with(False, None, True, 111111)

    @patch("fzfaws.s3.main.ls_s3")
    def test_ls(self, mocked_ls):
        s3(["ls"])
        mocked_ls.assert_called_with(False, False, False, False)

        s3(["ls", "-P", "-v", "-d", "-b"])
        mocked_ls.assert_called_with(True, True, True, True)

    @patch("fzfaws.s3.main.object_s3")
    def test_object(self, mocked_object):
        s3(["object"])
        mocked_object.assert_called_with(
            False, None, False, False, False, [], [], False
        )

        s3(["object", "-b", "hello", "-r", "-v", "-V", "-n"])
        mocked_object.assert_called_with(False, "hello", True, True, True, [], [], True)
