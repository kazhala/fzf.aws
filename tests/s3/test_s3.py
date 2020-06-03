import io
import json
import os
import sys
import unittest
from unittest.mock import PropertyMock, patch
from fzfaws.s3 import S3
from fzfaws.utils import FileLoader, Pyfzf, BaseSession
from botocore.stub import Stubber
import boto3
from fzfaws.utils.exceptions import InvalidS3PathPattern
from botocore.paginate import Paginator


class TestS3(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput
        fileloader = FileLoader()
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../../fzfaws.yml"
        )
        fileloader.load_config_file(config_path=config_path)
        self.s3 = S3()

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_constructor(self):
        self.assertEqual(self.s3.profile, "default")
        self.assertEqual(self.s3.region, "ap-southeast-2")
        self.assertEqual(self.s3.bucket_name, "")
        self.assertEqual(self.s3.path_list, [""])

        s3 = S3(profile="root", region="us-east-1")
        self.assertEqual(s3.profile, "root")
        self.assertEqual(s3.region, "us-east-1")
        self.assertEqual(s3.bucket_name, "")
        self.assertEqual(s3.path_list, [""])

    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Pyfzf, "process_list")
    def test_set_s3_bucket(self, mocked_list, mocked_execute, mocked_client):
        self.s3.bucket_name = ""
        self.s3.path_list = [""]
        s3_data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/s3_bucket.json"
        )
        with open(s3_data_path, "r") as file:
            response = json.load(file)

        # normal test
        s3 = boto3.client("s3")
        stubber = Stubber(s3)
        stubber.add_response("list_buckets", response)
        stubber.activate()
        mocked_client.return_value = s3
        mocked_execute.return_value = "kazhala-version-testing"
        self.s3.set_s3_bucket()
        self.assertEqual(self.s3.bucket_name, "kazhala-version-testing")
        mocked_list.assert_called_with(response["Buckets"], "Name")
        mocked_execute.assert_called_with(header="")

        # empty test
        s3 = boto3.client("s3")
        stubber = Stubber(s3)
        stubber.add_response("list_buckets", {"Buckets": []})
        stubber.activate()
        mocked_client.return_value = s3
        mocked_execute.return_value = ""
        self.s3.set_s3_bucket(header="hello")
        self.assertEqual(self.s3.bucket_name, "")
        mocked_list.assert_called_with([], "Name")
        mocked_execute.assert_called_with(header="hello")

    @patch.object(S3, "_validate_input_path")
    def test_set_bucket_and_path(self, mocked_validation):
        self.s3.bucket_name = ""
        self.s3.path_list = [""]
        self.s3.set_bucket_and_path(bucket="")

        mocked_validation.return_value = (
            "bucketpath",
            ("kazhala-version-testing/", ""),
        )
        self.s3.set_bucket_and_path(bucket="kazhala-version-testing/")
        self.assertEqual(self.s3.bucket_name, "kazhala-version-testing")
        self.assertEqual(self.s3.path_list, [""])

        mocked_validation.return_value = (
            "bucketpath",
            ("kazhala-version-testing/", "object1"),
        )
        self.s3.set_bucket_and_path(bucket="kazhala-version-testing/object1")
        self.assertEqual(self.s3.bucket_name, "kazhala-version-testing")
        self.assertEqual(self.s3.path_list, ["object1"])

        mocked_validation.return_value = (
            "bucketpath",
            ("kazhala-version-testing/", "folder/folder2/"),
        )
        self.s3.set_bucket_and_path(bucket="kazhala-version-testing/folder/folder2/")
        self.assertEqual(self.s3.bucket_name, "kazhala-version-testing")
        self.assertEqual(self.s3.path_list, ["folder/folder2/"])

        mocked_validation.return_value = (
            "bucketpath",
            ("kazhala-version-testing/", "folder/object1"),
        )
        self.s3.set_bucket_and_path(bucket="kazhala-version-testing/folder/object1")
        self.assertEqual(self.s3.bucket_name, "kazhala-version-testing")
        self.assertEqual(self.s3.path_list, ["folder/object1"])

        mocked_validation.return_value = (None, None)
        self.assertRaises(
            InvalidS3PathPattern,
            self.s3.set_bucket_and_path,
            bucket="kazhala-version-testing",
        )

        mocked_validation.return_value = (
            "accesspoint",
            ("arn:aws:s3:us-west-2:123456789012:accesspoint/test/", "object"),
        )
        self.s3.set_bucket_and_path(
            bucket="arn:aws:s3:us-west-2:123456789012:accesspoint/test/object"
        )
        self.assertEqual(
            self.s3.bucket_name, "arn:aws:s3:us-west-2:123456789012:accesspoint/test"
        )
        self.assertEqual(self.s3.path_list, ["object"])

    def test_validate_input_path(self):
        result, match = self.s3._validate_input_path("kazhala-version-testing/")
        self.assertEqual(result, "bucketpath")
        self.assertEqual(match, ("kazhala-version-testing/", ""))

        result, match = self.s3._validate_input_path("kazhala-version-testing")
        self.assertEqual(result, None)
        self.assertEqual(match, None)

        result, match = self.s3._validate_input_path("kazhala-version-testing/hello")
        self.assertEqual(result, "bucketpath")
        self.assertEqual(match, ("kazhala-version-testing/", "hello"))

        result, match = self.s3._validate_input_path(
            "kazhala-version-testing/hello/world"
        )
        self.assertEqual(result, "bucketpath")
        self.assertEqual(match, ("kazhala-version-testing/", "hello/world"))

        result, match = self.s3._validate_input_path(
            "arn:aws:s3:us-west-2:123456789012:accesspoint/test/hello"
        )
        self.assertEqual(result, "accesspoint")
        self.assertEqual(
            match, ("arn:aws:s3:us-west-2:123456789012:accesspoint/test/", "hello"),
        )

        result, match = self.s3._validate_input_path(
            "arn:aws:s3:us-west-2:123456789012:accesspoint/test/hello/world"
        )
        self.assertEqual(result, "accesspoint")
        self.assertEqual(
            match,
            ("arn:aws:s3:us-west-2:123456789012:accesspoint/test/", "hello/world"),
        )

        result, match = self.s3._validate_input_path(
            "arn:aws:s3:us-west-2:123456789012:accesspoint/test"
        )
        self.assertEqual(result, None)
        self.assertEqual(match, None)

    @patch("fzfaws.s3.s3.get_confirmation")
    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Pyfzf, "append_fzf")
    @patch.object(Paginator, "paginate")
    @patch("builtins.input")
    @patch.object(S3, "_get_path_option")
    def test_set_s3_path(
        self,
        mocked_option,
        mocked_input,
        mocked_paginator,
        mocked_append,
        mocked_execute,
        mocked_confirmation,
    ):
        # input
        self.s3.bucket_name = "kazhala-version-testing"
        mocked_option.return_value = "input"
        mocked_input.return_value = "hello"
        self.s3.set_s3_path()
        self.assertEqual(self.s3.path_list[0], "hello")

        # root
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        mocked_option.return_value = "root"
        self.s3.set_s3_path()
        self.assertEqual(
            self.capturedOutput.getvalue(), "S3 file path is set to root\n"
        )

        # interactively normal
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        self.s3.bucket_name = "kazhala-version-testing"
        self.s3.path_list = [""]
        mocked_option.return_value = "interactively"
        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/s3_object.json"
        )
        with open(data_path, "r") as file:
            response = json.load(file)
        mocked_paginator.return_value = response
        mocked_execute.return_value = ""
        mocked_confirmation.return_value = True
        self.s3.set_s3_path()
        mocked_execute.assert_called_with(
            empty_allow=True,
            print_col=0,
            header="PWD: s3://kazhala-version-testing/ (press ESC to use current path)",
            preview="echo .DS_Store Fortnite refund.docx README.md VideoPageSpec.docx boob.docx boto3-s3-filter.png cloudformation_parameters.png elb.pem lab.pem ooooo.doc version1.com version2.com version3.com | tr ' ' '\n'",
        )
        mocked_append.assert_called_with("versiontesting/\n")
        mocked_confirmation.assert_called()
        self.assertRegex(self.capturedOutput.getvalue(), "S3 file path is set to root")

        # interactively empty with path
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        mocked_paginator.return_value = []
        self.s3.bucket_name = "kazhala-version-testing"
        self.s3.path_list = ["hello/"]
        mocked_execute.return_value = ""
        mocked_confirmation.return_value = True
        self.s3.set_s3_path()
        mocked_execute.assert_called_with(
            empty_allow=True,
            print_col=0,
            header="PWD: s3://kazhala-version-testing/hello/ (press ESC to use current path)",
            preview="echo  | tr ' ' '\n'",
        )
        mocked_append.assert_called_with("versiontesting/\n")
        mocked_confirmation.assert_called()
        self.assertRegex(
            self.capturedOutput.getvalue(), "S3 file path is set to hello/"
        )

        # append normal
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        self.s3.bucket_name = "kazhala-version-testing"
        self.s3.path_list = [""]
        mocked_option.return_value = "append"
        mocked_paginator.return_value = response
        mocked_execute.return_value = ""
        mocked_confirmation.return_value = True
        mocked_input.return_value = "newpath/"
        self.s3.set_s3_path()
        mocked_execute.assert_called_with(
            empty_allow=True,
            print_col=0,
            header="PWD: s3://kazhala-version-testing/ (press ESC to use current path)",
            preview="echo .DS_Store Fortnite refund.docx README.md VideoPageSpec.docx boob.docx boto3-s3-filter.png cloudformation_parameters.png elb.pem lab.pem ooooo.doc version1.com version2.com version3.com | tr ' ' '\n'",
        )
        mocked_append.assert_called_with("versiontesting/\n")
        self.assertRegex(
            self.capturedOutput.getvalue(), "S3 file path is set to newpath/"
        )
        self.assertRegex(
            self.capturedOutput.getvalue(),
            "Current PWD is s3://kazhala-version-testing/",
        )
        self.assertEqual(self.s3.path_list, ["newpath/"])

        # append empty with path
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        self.s3.bucket_name = "kazhala-version-testing"
        self.s3.path_list = ["newpath/"]
        mocked_option.return_value = "append"
        mocked_paginator.return_value = response
        mocked_execute.return_value = ""
        mocked_confirmation.return_value = True
        mocked_input.return_value = "obj1"
        self.s3.set_s3_path()
        mocked_execute.assert_called_with(
            empty_allow=True,
            print_col=0,
            header="PWD: s3://kazhala-version-testing/newpath/ (press ESC to use current path)",
            preview="echo .DS_Store Fortnite refund.docx README.md VideoPageSpec.docx boob.docx boto3-s3-filter.png cloudformation_parameters.png elb.pem lab.pem ooooo.doc version1.com version2.com version3.com | tr ' ' '\n'",
        )
        mocked_append.assert_called_with("versiontesting/\n")
        self.assertRegex(
            self.capturedOutput.getvalue(), "S3 file path is set to newpath/obj1"
        )
        self.assertRegex(
            self.capturedOutput.getvalue(),
            "Current PWD is s3://kazhala-version-testing/newpath/",
        )
        self.assertEqual(self.s3.path_list, ["newpath/obj1"])
