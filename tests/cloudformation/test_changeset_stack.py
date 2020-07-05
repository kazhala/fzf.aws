from fzfaws.utils.pyfzf import Pyfzf
import io
import sys
import unittest
from unittest.mock import call, patch
from fzfaws.cloudformation.changeset_stack import changeset_stack


class TestCloudformationChangesetStack(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput
        self.list_change_sets_value = {
            "Summaries": [
                {
                    "ChangeSetName": "foo",
                    "StackName": "testing1",
                    "ExecutionStatus": "AVAILABLE",
                    "Status": "CREATE_COMPLETE",
                    "Description": "boo",
                }
            ]
        }

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch.object(Pyfzf, "process_list")
    @patch.object(Pyfzf, "execute_fzf")
    @patch("fzfaws.cloudformation.changeset_stack.Cloudformation")
    def test_changset_info(self, MockedCloudformation, mocked_execute, mocked_process):
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        cloudformation = MockedCloudformation()
        cloudformation.stack_name = "testing1"
        cloudformation.client.list_change_sets.return_value = (
            self.list_change_sets_value
        )
        mocked_execute.return_value = "fooboo"

        cloudformation.client.describe_change_set.return_value = {"Changes": {}}
        changeset_stack(info=True)
        cloudformation.set_stack.assert_called_once()
        cloudformation.client.list_change_sets.assert_called_once_with(
            StackName="testing1"
        )
        mocked_process.assert_called_once_with(
            self.list_change_sets_value["Summaries"],
            "ChangeSetName",
            "StackName",
            "ExecutionStatus",
            "Status",
            "Description",
        )
        mocked_execute.assert_called_once()
        cloudformation.client.describe_change_set.assert_called_once_with(
            ChangeSetName="fooboo", StackName="testing1"
        )
        self.assertRegex(self.capturedOutput.getvalue(), r"StackName: testing1")
        self.assertRegex(self.capturedOutput.getvalue(), r"ChangeSetName: fooboo")

    @patch("fzfaws.cloudformation.changeset_stack.get_confirmation")
    @patch.object(Pyfzf, "process_list")
    @patch.object(Pyfzf, "execute_fzf")
    @patch("fzfaws.cloudformation.changeset_stack.Cloudformation")
    def test_execute_changeset(
        self, MockedCloudformation, mocked_execute, mocked_list, mocked_confirm
    ):
        mocked_confirm.return_value = True
        cloudformation = MockedCloudformation()
        cloudformation.stack_name = "testing1"
        cloudformation.client.list_change_sets.return_value = (
            self.list_change_sets_value
        )
        mocked_execute.return_value = "fooboo"
        changeset_stack(execute=True, delete=True)
        cloudformation.client.delete_change_set.assert_not_called()
        cloudformation.set_stack.assert_called_once()
        cloudformation.client.list_change_sets.assert_called_once_with(
            StackName="testing1"
        )
        mocked_list.assert_called_once_with(
            self.list_change_sets_value["Summaries"],
            "ChangeSetName",
            "StackName",
            "ExecutionStatus",
            "Status",
            "Description",
        )
        cloudformation.client.execute_change_set.assert_called_once_with(
            ChangeSetName="fooboo", StackName="testing1"
        )
        cloudformation.wait.assert_called_once_with(
            "stack_update_complete", "Wating for stack to be updated ..."
        )

    @patch("fzfaws.cloudformation.changeset_stack.get_confirmation")
    @patch.object(Pyfzf, "process_list")
    @patch.object(Pyfzf, "execute_fzf")
    @patch("fzfaws.cloudformation.changeset_stack.Cloudformation")
    def test_delete_changeset(
        self, MockedCloudformation, mocked_execute, mocked_process, mocked_confirm,
    ):
        mocked_confirm.return_value = True
        cloudformation = MockedCloudformation()
        cloudformation.stack_name = "testing1"
        cloudformation.client.list_change_sets.return_value = (
            self.list_change_sets_value
        )
        mocked_execute.return_value = ["fooboo", "helloworld"]
        changeset_stack(delete=True)
        mocked_execute.assert_called_once_with(multi_select=True)
        cloudformation.client.delete_change_set.assert_has_calls(
            [
                call(ChangeSetName="fooboo", StackName="testing1"),
                call(ChangeSetName="helloworld", StackName="testing1"),
            ]
        )

    @patch("fzfaws.cloudformation.changeset_stack.update_stack")
    @patch("builtins.input")
    @patch("fzfaws.cloudformation.changeset_stack.Cloudformation")
    def test_create_changeset(self, MockedCloudformation, mocked_input, mocked_udpate):
        cloudformation = MockedCloudformation()
        cloudformation.stack_name = "testing1"
        mocked_input.return_value = "fooboo"
        mocked_udpate.return_value = {
            "Parameters": [
                {"ParameterKey": "SSHLocation", "UsePreviousValue": True},
                {"ParameterKey": "Hello", "UsePreviousValue": True},
                {"ParameterKey": "WebServer", "UsePreviousValue": True},
            ],
            "StackName": "testing1",
            "UsePreviousTemplate": True,
            "cloudformation_action": cloudformation.client.create_change_set,
        }
        cloudformation.execute_with_capabilities.return_value = {}
        changeset_stack(profile="root", region="us-east-1")
        cloudformation.execute_with_capabilities.assert_called_once_with(
            ChangeSetName="fooboo",
            Description="fooboo",
            Parameters=[
                {"ParameterKey": "SSHLocation", "UsePreviousValue": True},
                {"ParameterKey": "Hello", "UsePreviousValue": True},
                {"ParameterKey": "WebServer", "UsePreviousValue": True},
            ],
            StackName="testing1",
            UsePreviousTemplate=True,
            cloudformation_action=cloudformation.client.create_change_set,
        )
        mocked_udpate.assert_called_once_with(
            cloudformation.profile,
            cloudformation.region,
            False,
            False,
            False,
            False,
            False,
            None,
            False,
            cloudformation=cloudformation,
            dryrun=True,
        )
        MockedCloudformation.assert_called_with("root", "us-east-1")

        changeset_stack(
            replace=True, wait=True, extra=True, bucket="kazhala-lol/hello.yaml"
        )
        MockedCloudformation.assert_called_with(False, False)
        mocked_udpate.assert_called_with(
            cloudformation.profile,
            cloudformation.region,
            True,
            False,
            False,
            True,
            True,
            "kazhala-lol/hello.yaml",
            False,
            cloudformation=cloudformation,
            dryrun=True,
        )
