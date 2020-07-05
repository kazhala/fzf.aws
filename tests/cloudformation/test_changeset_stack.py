from fzfaws.utils.pyfzf import Pyfzf
import io
import sys
import unittest
from unittest.mock import patch
from fzfaws.cloudformation.changeset_stack import changeset_stack


class TestCloudformationChangesetStack(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

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
        cloudformation.client.list_change_sets.return_value = {
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
        mocked_execute.return_value = "fooboo"

        cloudformation.client.describe_change_set.return_value = {"Changes": {}}
        changeset_stack(info=True)
        cloudformation.set_stack.assert_called_once()
        cloudformation.client.list_change_sets.assert_called_once_with(
            StackName="testing1"
        )
        mocked_process.assert_called_once_with(
            [
                {
                    "ChangeSetName": "foo",
                    "StackName": "testing1",
                    "ExecutionStatus": "AVAILABLE",
                    "Status": "CREATE_COMPLETE",
                    "Description": "boo",
                }
            ],
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
