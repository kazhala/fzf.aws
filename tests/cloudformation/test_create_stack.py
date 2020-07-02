import io
import os
import sys
import unittest
from unittest.mock import ANY, patch

from fzfaws.cloudformation.cloudformation import Cloudformation
from fzfaws.cloudformation.create_stack import create_stack
from fzfaws.cloudformation.helper.paramprocessor import ParamProcessor
from fzfaws.utils.pyfzf import Pyfzf


class TestCloudformationCreateStack(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch.object(ParamProcessor, "process_stack_params")
    @patch.object(Cloudformation, "wait")
    @patch.object(Cloudformation, "execute_with_capabilities")
    @patch("builtins.input")
    @patch("fzfaws.cloudformation.create_stack.validate_stack")
    @patch.object(Pyfzf, "get_local_file")
    def test_local_creation(
        self,
        mocked_local,
        mocked_validate,
        mocked_input,
        mocked_execute,
        mocked_wait,
        mocked_process,
    ):

        mocked_input.return_value = "testing_stack"
        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../data/cloudformation_template.yaml",
        )
        mocked_local.return_value = data_path
        create_stack(local_path=True, root=True, wait=True)

        mocked_local.assert_called_with(search_from_root=True, cloudformation=True)
        mocked_validate.assert_called_with(
            None, None, local_path=data_path, no_print=True
        )
        mocked_execute.assert_called_with(
            Parameters=[],
            StackName="testing_stack",
            TemplateBody=ANY,
            cloudformation_action=ANY,
        )
        mocked_wait.assert_called_with(
            "stack_create_complete", "Waiting for stack to be ready ..."
        )

        mocked_local.reset_mock()
        create_stack(
            profile="root", region="us-east-1", local_path=data_path, wait=True
        )
        mocked_local.assert_not_called()
        mocked_validate.assert_called_with(
            "root", "us-east-1", local_path=data_path, no_print=True
        )
        mocked_execute.assert_called_with(
            Parameters=[],
            StackName="testing_stack",
            TemplateBody=ANY,
            cloudformation_action=ANY,
        )
        mocked_wait.assert_called_with(
            "stack_create_complete", "Waiting for stack to be ready ..."
        )
