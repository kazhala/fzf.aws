import json
from fzfaws.utils.pyfzf import Pyfzf
import os
import io
import sys
import unittest
from unittest.mock import patch
from fzfaws.cloudformation import Cloudformation
from botocore.paginate import Paginator


class TestCloudformation(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput
        self.cloudformation = Cloudformation()

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_constructor(self):
        self.assertEqual(self.cloudformation.region, None)
        self.assertEqual(self.cloudformation.profile, None)
        self.assertEqual(self.cloudformation.stack_name, "")
        self.assertEqual(self.cloudformation.stack_details, {})

        cloudformation = Cloudformation(profile="root", region="us-east-1")
        self.assertEqual(cloudformation.region, "us-east-1")
        self.assertEqual(cloudformation.profile, "root")
        self.assertEqual(cloudformation.stack_name, "")
        self.assertEqual(cloudformation.stack_details, {})

    @patch.object(Paginator, "paginate")
    @patch.object(Pyfzf, "process_list")
    @patch.object(Pyfzf, "execute_fzf")
    def test_set_stack(self, mocked_execute, mocked_list, mocked_page):
        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../data/cloudformation_stacks.json",
        )
        with open(data_path, "r") as file:
            response = json.load(file)

        mocked_page.return_value = response
        mocked_execute.return_value = "dotbare-cicd"
        self.cloudformation.set_stack()
        mocked_list.assert_called_once_with(
            response[0]["Stacks"], "StackName", "StackStatus", "Description"
        )
        mocked_execute.assert_called_once_with(empty_allow=False)
        self.assertEqual(
            self.cloudformation.stack_details,
            {
                "Capabilities": ["CAPABILITY_NAMED_IAM"],
                "Description": "CodeBuild template for dotbare, webhook trigger from Github "
                "only on Master push",
                "DisableRollback": False,
                "DriftInformation": {"StackDriftStatus": "IN_SYNC"},
                "NotificationARNs": [],
                "RollbackConfiguration": {"RollbackTriggers": []},
                "StackId": "arn:aws:cloudformation:ap-southeast-2:1111111:stack/dotbare-cicd/0ae5ef60-9651-11ea-b6d0-0223bf2782f0",
                "StackName": "dotbare-cicd",
                "StackStatus": "UPDATE_COMPLETE",
                "Tags": [],
            },
        )
        self.assertEqual(self.cloudformation.stack_name, "dotbare-cicd")

        mocked_list.reset_mock()
        mocked_execute.reset_mock()
        mocked_execute.return_value = "hellotesting"
        self.cloudformation.set_stack()
        mocked_list.assert_called_once_with(
            response[0]["Stacks"], "StackName", "StackStatus", "Description"
        )
        mocked_execute.assert_called_once_with(empty_allow=False)
        self.assertEqual(
            self.cloudformation.stack_details,
            {
                "Description": "testing purposes only",
                "DisableRollback": False,
                "DriftInformation": {"StackDriftStatus": "IN_SYNC"},
                "NotificationARNs": [],
                "Outputs": [
                    {
                        "Description": "The security group id for EC2 import reference",
                        "ExportName": "hellotesting-SecurityGroupId",
                        "OutputKey": "SecurityGroupId",
                        "OutputValue": "sg-006ae18653dc5acd7",
                    }
                ],
                "Parameters": [
                    {"ParameterKey": "SSHLocation", "ParameterValue": "0.0.0.0/0"},
                    {"ParameterKey": "Hello", "ParameterValue": "i-0a23663d658dcee1c"},
                    {"ParameterKey": "WebServer", "ParameterValue": "No"},
                ],
                "RoleARN": "arn:aws:iam::1111111:role/admincloudformaitontest",
                "RollbackConfiguration": {},
                "StackId": "arn:aws:cloudformation:ap-southeast-2:1111111:stack/hellotesting/05feb330-88f3-11ea-ae79-0aa5d4eec80a",
                "StackName": "hellotesting",
                "StackStatus": "UPDATE_COMPLETE",
                "Tags": [{"Key": "hasdf", "Value": "asdfa"}],
            },
        )
        self.assertEqual(self.cloudformation.stack_name, "hellotesting")

    @patch.object(Paginator, "paginate")
    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Pyfzf, "process_list")
    def test_get_stack_resources(self, mocked_process, mocked_execute, mocked_page):
        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../data/cloudformation_resources.json",
        )
        with open(data_path, "r") as file:
            response = json.load(file)

        mocked_page.return_value = response
        mocked_execute.return_value = ["CodeBuild"]
        result = self.cloudformation.get_stack_resources()
        self.assertEqual(result, ["CodeBuild"])
        mocked_process.assert_called_once_with(
            [
                {
                    "LogicalResourceId": "CodeBuild",
                    "PhysicalResourceId": "dotbare",
                    "ResourceType": "AWS::CodeBuild::Project",
                    "ResourceStatus": "UPDATE_COMPLETE",
                    "DriftInformation": {"StackResourceDriftStatus": "NOT_CHECKED"},
                    "Drift": "NOT_CHECKED",
                },
                {
                    "LogicalResourceId": "ParameterStorePolicy",
                    "PhysicalResourceId": "dotba-Para-1G3Z5VTARYKOM",
                    "ResourceType": "AWS::IAM::Policy",
                    "ResourceStatus": "UPDATE_COMPLETE",
                    "DriftInformation": {"StackResourceDriftStatus": "NOT_CHECKED"},
                    "Drift": "NOT_CHECKED",
                },
                {
                    "LogicalResourceId": "ServiceRole",
                    "PhysicalResourceId": "dotbare-cicd-codebuild",
                    "ResourceType": "AWS::IAM::Role",
                    "ResourceStatus": "CREATE_COMPLETE",
                    "DriftInformation": {"StackResourceDriftStatus": "IN_SYNC"},
                    "Drift": "IN_SYNC",
                },
            ],
            "LogicalResourceId",
            "ResourceType",
            "Drift",
        )
        mocked_execute.assert_called_once_with(multi_select=True, empty_allow=False)

        mocked_process.reset_mock()
        mocked_execute.reset_mock()
        mocked_execute.return_value = ["hello"]
        result = self.cloudformation.get_stack_resources(empty_allow=True)
        self.assertEqual(result, ["hello"])
        mocked_process.assert_called_once()
        mocked_execute.assert_called_once_with(multi_select=True, empty_allow=True)
