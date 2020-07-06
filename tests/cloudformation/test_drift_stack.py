import os
import io
import sys
import unittest
from unittest.mock import patch
from fzfaws.cloudformation.drift_stack import drift_stack


class TestCloudformationDriftStack(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch("fzfaws.cloudformation.drift_stack.Cloudformation")
    def test_info(self, MockedCloudformation):
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        cloudformation = MockedCloudformation()
        cloudformation.stack_details = {
            "StackId": "arn:aws:cloudformation:ap-southeast-2:1111111:stack/dotbare-cicd/0ae5ef60-9651-11ea-b6d0-0223bf2782f0",
            "StackName": "dotbare-cicd",
            "Description": "CodeBuild template for dotbare, webhook trigger from Github only on Master push",
            "RollbackConfiguration": {"RollbackTriggers": []},
            "StackStatus": "UPDATE_COMPLETE",
            "DisableRollback": False,
            "NotificationARNs": [],
            "Capabilities": ["CAPABILITY_NAMED_IAM"],
            "Tags": [],
            "DriftInformation": {"StackDriftStatus": "IN_SYNC"},
        }
        cloudformation.stack_name = "testing1"
        cloudformation.client.describe_stack_resource_drifts.return_value = {}
        drift_stack(profile="root", region="us-east-1", info=True)
        MockedCloudformation.assert_called_with("root", "us-east-1")
        cloudformation.set_stack.assert_called_once()
        cloudformation.client.describe_stack_resource_drifts.assert_called_once_with(
            StackName="testing1"
        )
        self.assertRegex(
            self.capturedOutput.getvalue(), r'"StackDriftStatus": "IN_SYNC"'
        )
