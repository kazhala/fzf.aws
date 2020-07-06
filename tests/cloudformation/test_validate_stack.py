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
