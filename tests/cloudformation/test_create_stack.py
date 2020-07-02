from fzfaws.cloudformation.helper.cloudformationargs import CloudformationArgs
from fzfaws.s3.s3 import S3
import io
import os
import sys
import unittest
from unittest.mock import ANY, patch

from fzfaws.cloudformation.cloudformation import Cloudformation
from fzfaws.cloudformation.create_stack import create_stack
from fzfaws.cloudformation.helper.paramprocessor import ParamProcessor
from fzfaws.utils import Pyfzf, FileLoader


class TestCloudformationCreateStack(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        self.data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../data/cloudformation_template.yaml",
        )
        sys.stdout = self.capturedOutput
        fileloader = FileLoader()
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../../fzfaws.yml"
        )
        fileloader.load_config_file(config_path=config_path)

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
        self.data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../data/cloudformation_template.yaml",
        )
        mocked_local.return_value = self.data_path
        create_stack(local_path=True, root=True, wait=True)

        mocked_local.assert_called_with(search_from_root=True, cloudformation=True)
        mocked_validate.assert_called_with(
            "default", "ap-southeast-2", local_path=self.data_path, no_print=True
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
            profile="root", region="us-east-1", local_path=self.data_path, wait=True
        )
        mocked_local.assert_not_called()
        mocked_validate.assert_called_with(
            "root", "us-east-1", local_path=self.data_path, no_print=True
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

    @patch.object(ParamProcessor, "process_stack_params")
    @patch.object(Cloudformation, "wait")
    @patch.object(Cloudformation, "execute_with_capabilities")
    @patch("builtins.input")
    @patch("fzfaws.cloudformation.create_stack.validate_stack")
    @patch.object(S3, "get_object_url")
    @patch.object(S3, "get_object_data")
    @patch.object(S3, "get_object_version")
    def test_s3_creation(
        self,
        mocked_version,
        mocked_data,
        mocked_url,
        mocked_validate,
        mocked_input,
        mocked_execute,
        mocked_wait,
        mocked_process,
    ):
        mocked_input.return_value = "testing_stack"
        mocked_version.return_value = [{"VersionId": "111111"}]
        fileloader = FileLoader(self.data_path)
        mocked_data.return_value = fileloader.process_yaml_file()
        mocked_url.return_value = "https://s3-ap-southeast-2.amazonaws.com/kazhala-lol/hello.yaml?versionId=111111"

        create_stack(bucket="kazhala-lol/hello.yaml", version=True)
        mocked_version.assert_called_with("kazhala-lol", "hello.yaml")
        mocked_validate.assert_called_with(
            "default",
            "ap-southeast-2",
            bucket="kazhala-lol/hello.yaml",
            version="111111",
            no_print=True,
        )
        mocked_data.assert_called_with("yaml")
        mocked_url.assert_called_with(version="111111")
        mocked_execute.assert_called_with(
            Parameters=[],
            StackName="testing_stack",
            TemplateURL="https://s3-ap-southeast-2.amazonaws.com/kazhala-lol/hello.yaml?versionId=111111",
            cloudformation_action=ANY,
        )
        mocked_wait.assert_not_called()

        mocked_version.reset_mock()
        create_stack(
            profile="root",
            region="us-east-1",
            bucket="kazhala-lol/hello.yaml",
            version="111111",
            wait=True,
        )
        mocked_version.assert_not_called()
        mocked_validate.assert_called_with(
            "root",
            "us-east-1",
            bucket="kazhala-lol/hello.yaml",
            version="111111",
            no_print=True,
        )
        mocked_data.assert_called_with("yaml")
        mocked_url.assert_called_with(version="111111")
        mocked_execute.assert_called_with(
            Parameters=[],
            StackName="testing_stack",
            TemplateURL="https://s3-ap-southeast-2.amazonaws.com/kazhala-lol/hello.yaml?versionId=111111",
            cloudformation_action=ANY,
        )
        mocked_wait.assert_called_with(
            "stack_create_complete", "Waiting for stack to be ready ..."
        )

    @patch.object(Cloudformation, "wait")
    @patch.object(Cloudformation, "execute_with_capabilities")
    @patch.object(CloudformationArgs, "set_extra_args")
    @patch("fzfaws.cloudformation.create_stack.construct_s3_creation_args")
    def test_create_stack_with_extra(
        self, mocked_args, mocked_set_args, mocked_execute, mocked_wait
    ):
        mocked_args.return_value = {"StackName": "testing_stack"}
        create_stack(wait=True, extra=True)
        mocked_execute.assert_called_with(StackName="testing_stack")
        mocked_set_args.assert_called_with(search_from_root=False)
        mocked_wait.assert_called_once()
