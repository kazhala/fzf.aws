import os
from fzfaws.utils.pyfzf import Pyfzf
import io
import sys
import unittest
from unittest.mock import patch
from fzfaws.cloudformation.validate_stack import validate_stack


class TestCloudformationValidateStack(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput
        self.response = {
            "Parameters": [
                {
                    "ParameterKey": "foo",
                    "DefaultValue": "boo",
                    "NoEcho": True,
                    "Description": "hello world",
                },
            ],
            "Description": "lolololo",
            "Capabilities": ["CAPABILITY_IAM"],
            "CapabilitiesReason": "IAM",
        }

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch.object(Pyfzf, "get_local_file")
    @patch("fzfaws.cloudformation.validate_stack.Cloudformation")
    def test_local_validate(self, MockedCloudformation, mocked_local):
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        template_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../data/cloudformation_template.yaml",
        )
        mocked_local.return_value = template_path
        cloudformation = MockedCloudformation()
        cloudformation.client.validate_template.return_value = self.response
        validate_stack(local_path=True, root=True)
        mocked_local.assert_called_once_with(
            search_from_root=True,
            cloudformation=True,
            header="select a cloudformation template to validate",
        )
        cloudformation.client.validate_template.assert_called_once()
        self.assertRegex(self.capturedOutput.getvalue(), r'"ParameterKey": "foo"')
        self.assertRegex(self.capturedOutput.getvalue(), r'"DefaultValue": "boo"')

        mocked_local.reset_mock()
        cloudformation.client.validate_template.reset_mock()
        validate_stack(local_path=template_path)
        mocked_local.assert_not_called()
        cloudformation.client.validate_template.assert_called_once()

    @patch("fzfaws.cloudformation.validate_stack.S3")
    @patch("fzfaws.cloudformation.validate_stack.Cloudformation")
    def test_s3_validate(self, MockedCloudformation, MockedS3):
        cloudformation = MockedCloudformation()
        cloudformation.client.validate_template.return_value = self.response
        s3 = MockedS3()
        s3.bucket_name = "kazhala-lol"
        s3.path_list = ["hello.yaml"]
        s3.get_object_url.return_value = (
            "https://s3-ap-southeast-2.amazonaws.com/kazhala-lol/hello.yaml"
        )
        s3.get_object_version.return_value = [{"VersionId": "111111"}]
        validate_stack(profile="root", region="ap-southeast-2")
        MockedS3.assert_called_with("root", "ap-southeast-2")
        MockedCloudformation.assert_called_with("root", "ap-southeast-2")
        s3.get_object_url.assert_called_once_with("")
        cloudformation.client.validate_template.assert_called_once_with(
            TemplateURL="https://s3-ap-southeast-2.amazonaws.com/kazhala-lol/hello.yaml"
        )
        self.assertRegex(self.capturedOutput.getvalue(), r'"ParameterKey": "foo"')
        self.assertRegex(self.capturedOutput.getvalue(), r'"DefaultValue": "boo"')

        s3.get_object_url.reset_mock()
        cloudformation.client.validate_template.reset_mock()
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        s3.bucket_name = ""
        s3.path_list = ["hello.yaml"]
        s3.get_object_url.return_value = "https://s3-ap-southeast-2.amazonaws.com/kazhala-lol/hello.yaml?versionid=111111"
        validate_stack(no_print=True, bucket="kazhala-lol/", version=True)
        s3.set_s3_bucket.assert_called_once_with(
            header="select a bucket which contains the template"
        )
        s3.get_object_url.assert_called_once_with("111111")
        cloudformation.client.validate_template.assert_called_once_with(
            TemplateURL="https://s3-ap-southeast-2.amazonaws.com/kazhala-lol/hello.yaml?versionid=111111"
        )

        self.assertNotRegex(self.capturedOutput.getvalue(), r'"ParameterKey": "foo"')
        self.assertNotRegex(self.capturedOutput.getvalue(), r'"DefaultValue": "boo"')
