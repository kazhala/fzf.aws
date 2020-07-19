import os
import io
import sys
import unittest
from unittest.mock import patch
from fzfaws.cloudformation.delete_stack import delete_stack


class TestCloudformationDeleteStack(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch("fzfaws.cloudformation.delete_stack.get_confirmation")
    @patch("fzfaws.cloudformation.delete_stack.Cloudformation")
    def test_normal_delete(self, MockedCloudformation, mocked_confirm):
        mocked_confirm.return_value = True
        cloudformation = MockedCloudformation()
        cloudformation.stack_name = "testing1"
        cloudformation.stack_details = {"StackStatus": "UPDATE_COMPLETE"}
        delete_stack()
        cloudformation.set_stack.assert_called_once()
        mocked_confirm.assert_called_with(
            "Are you sure you want to delete the stack 'testing1'?"
        )
        cloudformation.client.delete_stack.assert_called_with(StackName="testing1")
        cloudformation.client.wait.assert_not_called()

        delete_stack(wait=True, profile="root", region="us-east-1")
        MockedCloudformation.assert_called_with("root", "us-east-1")
        cloudformation.wait.assert_called_once_with(
            "stack_delete_complete", "Wating for stack to be deleted ..."
        )

    @patch("fzfaws.cloudformation.delete_stack.get_confirmation")
    @patch("fzfaws.cloudformation.delete_stack.Cloudformation")
    def test_retain_delete(self, MockedCloudformation, mocked_confirm):
        mocked_confirm.return_value = True
        cloudformation = MockedCloudformation()
        cloudformation.stack_name = "testing1"
        cloudformation.stack_details = {"StackStatus": "DELETE_FAILED"}
        cloudformation.get_stack_resources.return_value = ["S3Bucket", "OAI"]
        delete_stack()
        cloudformation.set_stack.assert_called_once()
        mocked_confirm.assert_called_with(
            "Are you sure you want to delete the stack 'testing1'?"
        )
        cloudformation.get_stack_resources.assert_called_once_with(
            empty_allow=True,
            header="stack is in the failed state, specify any resource to skip during deletion",
        )
        cloudformation.client.delete_stack.assert_called_with(
            RetainResources=["S3Bucket", "OAI"], StackName="testing1"
        )
        cloudformation.wait.assert_not_called()

    @patch("fzfaws.cloudformation.delete_stack.IAM")
    @patch("fzfaws.cloudformation.delete_stack.get_confirmation")
    @patch("fzfaws.cloudformation.delete_stack.Cloudformation")
    def test_iam_delete(self, MockedCloudformation, mocked_confirm, MockedIAM):
        mocked_confirm.return_value = True
        iam = MockedIAM()
        iam.arns = ["111111"]
        cloudformation = MockedCloudformation()
        cloudformation.stack_name = "testing1"
        cloudformation.stack_details = {"StackStatus": "CREATE_COMPLETE"}
        delete_stack(iam=True)
        iam.set_arns.assert_called_once_with(
            header="select a iam role with permissions to delete the current stack",
            service="cloudformation.amazonaws.com",
        )
        cloudformation.client.delete_stack.assert_called_with(
            RoleARN="111111", StackName="testing1"
        )

        iam.set_arns.reset_mock()
        delete_stack(iam="222222")
        iam.set_arns.assert_not_called()
        cloudformation.client.delete_stack.assert_called_with(
            RoleARN="222222", StackName="testing1"
        )
