import io
import sys
import unittest
from unittest.mock import call, patch
from fzfaws.s3.bucket_s3 import bucket_s3, process_path_param
from fzfaws.s3 import S3


class TestS3BucketCopy(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch.object(S3, "set_s3_bucket")
    @patch.object(S3, "get_object_version")
    @patch.object(S3, "set_s3_object")
    @patch.object(S3, "set_s3_path")
    @patch("fzfaws.s3.bucket_s3.sync_s3")
    def test_sync(
        self, mocked_sync, mocked_path, mocked_object, mocked_version, mocked_bucket
    ):
        bucket_s3(sync=True, exclude=["*"], include=["hello*"])
        mocked_object.assert_not_called()
        mocked_version.assert_not_called()
        mocked_bucket.assert_has_calls(
            [
                call(
                    header="set the source bucket which contains the file to transfer"
                ),
                call(
                    header="set the destination bucket where the file should be transfered"
                ),
            ]
        )
        mocked_sync.assert_called_with(["*"], ["hello*"], "s3:///", "s3:///")

        bucket_s3(
            sync=True,
            exclude=["*"],
            include=["hello*"],
            from_bucket="kazhala-lol/",
            to_bucket="kazhala-yes/foo/",
            version=True,
        )
        mocked_version.assert_not_called()
        mocked_object.assert_not_called()
        mocked_sync.assert_called_with(
            ["*"], ["hello*"], "s3://kazhala-lol/", "s3://kazhala-yes/foo/"
        )

    @patch.object(S3, "set_s3_path")
    @patch.object(S3, "set_s3_bucket")
    @patch.object(S3, "get_object_version")
    @patch("fzfaws.s3.bucket_s3.walk_s3_folder")
    @patch("fzfaws.s3.bucket_s3.get_confirmation")
    def test_recusive(
        self, mocked_confirm, mocked_walk, mocked_version, mocked_bucket, mocked_path
    ):
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        mocked_confirm.return_value = False
        mocked_walk.side_effect = lambda a, b, c, d, e, g, h, i, j, k: print(
            b, c, d, e, g, h, i, j, k
        )
        bucket_s3(
            recursive=True,
            from_bucket="kazhala-lol/hello/",
            to_bucket="kazhala-yes/foo/",
            exclude=["*"],
            include=["foo*"],
            version=True,
        )
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "kazhala-lol hello/ hello/ [] ['*'] ['foo*'] bucket foo/ kazhala-yes\n",
        )
        mocked_version.assert_not_called()

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        bucket_s3(recursive=True)
        self.assertEqual(
            self.capturedOutput.getvalue(), "   [] [] [] bucket  \n",
        )
        mocked_bucket.assert_has_calls(
            [
                call(
                    header="set the source bucket which contains the file to transfer"
                ),
                call(
                    header="set the destination bucket where the file should be transfered"
                ),
            ]
        )
        mocked_path.assert_has_calls([call(), call()])

    @patch.object(S3, "set_s3_path")
    @patch.object(S3, "set_s3_object")
    @patch.object(S3, "set_s3_bucket")
    @patch.object(S3, "get_object_version")
    @patch("fzfaws.s3.bucket_s3.get_confirmation")
    def test_version(
        self, mocked_confirm, mocked_version, mocked_bucket, mocked_obj, mocked_path
    ):
        mocked_confirm.return_value = False
        mocked_version.return_value = [{"Key": "hello.txt", "VersionId": "11111111"}]

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        bucket_s3(
            from_bucket="kazhala-lol/hello.txt",
            to_bucket="kazhala-yes/foo/",
            version=True,
        )
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) copy: s3://kazhala-lol/hello.txt to s3://kazhala-yes/foo/hello.txt with version 11111111\n",
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        mocked_version.return_value = [{"Key": "hello.txt", "VersionId": "11111111"}]
        bucket_s3(version=True)
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) copy: s3:///hello.txt to s3:///hello.txt with version 11111111\n",
        )
        mocked_bucket.assert_has_calls(
            [
                call(
                    header="set the source bucket which contains the file to transfer"
                ),
                call(
                    header="set the destination bucket where the file should be transfered"
                ),
            ]
        )
        mocked_obj.assert_has_calls([call(multi_select=True, version=True)])
        mocked_path.assert_called_once()

    @patch.object(S3, "set_s3_path")
    @patch.object(S3, "set_s3_object")
    @patch.object(S3, "set_s3_bucket")
    @patch("fzfaws.s3.bucket_s3.get_confirmation")
    def test_single(self, mocked_confirm, mocked_bucket, mocked_object, mocked_path):
        mocked_confirm.return_value = False
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        bucket_s3()
        mocked_bucket.assert_has_calls(
            [
                call(
                    header="set the source bucket which contains the file to transfer"
                ),
                call(
                    header="set the destination bucket where the file should be transfered"
                ),
            ]
        )
        mocked_object.assert_has_calls([call(multi_select=True, version=False)])
        mocked_path.assert_called_once()
        self.assertEqual(
            self.capturedOutput.getvalue(), "(dryrun) copy: s3:/// to s3:///\n"
        )

        mocked_object.reset_mock()
        mocked_bucket.reset_mock()
        mocked_path.reset_mock()
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        bucket_s3(from_bucket="kazhala-lol/hello.txt", to_bucket="kazhala-yes/foo/")
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) copy: s3://kazhala-lol/hello.txt to s3://kazhala-yes/foo/hello.txt\n",
        )
        mocked_object.assert_not_called()
        mocked_path.assert_not_called()
        mocked_bucket.assert_not_called()

    @patch.object(S3, "set_s3_object")
    @patch.object(S3, "set_s3_path")
    def test_process_path_param(self, mocked_path, mocked_object):
        s3 = S3()
        result = process_path_param(
            bucket="kazhala-lol/", s3=s3, search_folder=True, version=False
        )
        self.assertEqual(result, ("kazhala-lol", "", [""]))
        mocked_path.assert_called_with()

        s3 = S3()
        result = process_path_param(
            bucket="kazhala-lol/hello.txt", s3=s3, search_folder=False, version=False
        )
        self.assertEqual(result, ("kazhala-lol", "hello.txt", ["hello.txt"]))
        mocked_object.assert_not_called()

        s3 = S3()
        s3.bucket_name = "lol"
        result = process_path_param(bucket="", s3=s3, search_folder=False, version=True)
        self.assertEqual(result, ("lol", "", [""]))
        mocked_object.assert_called_with(multi_select=True, version=True)

    @patch("fzfaws.s3.bucket_s3.walk_s3_folder")
    @patch.object(S3, "set_s3_path")
    @patch.object(S3, "get_object_version")
    @patch("fzfaws.s3.bucket_s3.get_confirmation")
    @patch("fzfaws.s3.bucket_s3.copy_and_preserve")
    def test_copy_and_preserve(
        self, mocked_copy, mocked_confirm, mocked_version, mocked_path, mocked_walk
    ):
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        mocked_copy.side_effect = lambda a, b, c, d, e: print(b, c, d, e)
        mocked_confirm.return_value = True
        bucket_s3(from_bucket="foo/boo.txt", to_bucket="lol/hello/", preserve=True)
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) copy: s3://foo/boo.txt to s3://lol/hello/boo.txt\ncopy: s3://foo/boo.txt to s3://lol/hello/boo.txt\nfoo boo.txt lol hello/boo.txt\n",
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        mocked_copy.side_effect = lambda a, b, c, d, e, version=None: print(
            b, c, d, e, version
        )
        mocked_confirm.return_value = True
        mocked_version.return_value = [{"Key": "boo.txt", "VersionId": "11111111"}]
        bucket_s3(
            from_bucket="foo/boo.txt",
            to_bucket="lol/hello/",
            preserve=True,
            version=True,
        )
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "(dryrun) copy: s3://foo/boo.txt to s3://lol/hello/boo.txt with version 11111111\ncopy: s3://foo/boo.txt to s3://lol/hello/boo.txt with version 11111111\nfoo boo.txt lol hello/boo.txt 11111111\n",
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        mocked_copy.side_effect = lambda a, b, c, d, e: print(b, c, d, e)
        mocked_confirm.return_value = True
        mocked_walk.return_value = [("boo/hello.txt", "hello/hello.txt")]
        bucket_s3(
            from_bucket="foo/boo/",
            to_bucket="lol/hello/",
            recursive=True,
            preserve=True,
        )
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "copy: s3://foo/boo/hello.txt to s3://lol/hello/hello.txt\nfoo boo/hello.txt lol hello/hello.txt\n",
        )
