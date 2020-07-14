import io
import json
import os
import sys
import unittest
from unittest.mock import ANY, call, patch

from botocore.paginate import Paginator
from botocore.waiter import Waiter

from fzfaws.cloudformation import Cloudformation
from fzfaws.utils import FileLoader
from fzfaws.utils.pyfzf import Pyfzf


class TestCloudformation(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput
        self.cloudformation = Cloudformation()
        fileloader = FileLoader()
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../../fzfaws/fzfaws.yml"
        )
        fileloader.load_config_file(config_path=config_path)

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
        mocked_execute.assert_called_once_with(
            multi_select=True, header=None, empty_allow=False
        )

        mocked_process.reset_mock()
        mocked_execute.reset_mock()
        mocked_execute.return_value = ["hello"]
        result = self.cloudformation.get_stack_resources(
            empty_allow=True, header="hello"
        )
        self.assertEqual(result, ["hello"])
        mocked_process.assert_called_once()
        mocked_execute.assert_called_once_with(
            multi_select=True, header="hello", empty_allow=True
        )

    @patch.object(Waiter, "wait")
    def test_wait(self, mocked_wait):
        self.cloudformation.stack_name = "dotbare-cicd"
        self.cloudformation.wait(waiter_name="stack_create_complete", message="hello")
        mocked_wait.assert_called_once_with(
            ANY,
            StackName="dotbare-cicd",
            WaiterConfig={"Delay": 30, "MaxAttempts": 120},
        )

        # test no config for watier
        mocked_wait.reset_mock()
        del os.environ["FZFAWS_CLOUDFORMATION_WAITER"]
        self.cloudformation.stack_name = "fooboo"
        self.cloudformation.wait(waiter_name="stack_create_complete", message="hello")
        mocked_wait.assert_called_once_with(
            ANY, StackName="fooboo", WaiterConfig={"Delay": 15, "MaxAttempts": 40},
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        # test no global waiter
        mocked_wait.reset_mock()
        del os.environ["FZFAWS_GLOBAL_WAITER"]
        self.cloudformation.stack_name = "yes"
        self.cloudformation.wait(
            waiter_name="stack_create_complete", message="hello", foo="boo"
        )
        mocked_wait.assert_called_once_with(
            ANY,
            StackName="yes",
            WaiterConfig={"Delay": 30, "MaxAttempts": 120},
            foo="boo",
        )
        self.assertRegex(self.capturedOutput.getvalue(), r"hello")

    @patch("fzfaws.cloudformation.cloudformation.get_confirmation")
    def test_execute_with_capabilities(self, mocked_confirm):
        def hello(**kwargs):
            return {**kwargs}

        mocked_confirm.return_value = True

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        result = self.cloudformation.execute_with_capabilities(
            hello, foo="boo", lol="yes"
        )
        self.assertEqual(result, {"foo": "boo", "lol": "yes"})
        self.assertEqual(
            self.capturedOutput.getvalue(),
            json.dumps({"foo": "boo", "lol": "yes"}, indent=4) + "\n",
        )

        mocked_confirm.return_value = False
        self.assertRaises(SystemExit, self.cloudformation.execute_with_capabilities)

    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Pyfzf, "append_fzf")
    def test_get_capabilities(self, mocked_append, mocked_execute):
        mocked_execute.return_value = ["CAPABILITY_IAM"]
        result = self.cloudformation._get_capabilities(message="lol")
        mocked_append.assert_has_calls(
            [
                call("CAPABILITY_IAM\n"),
                call("CAPABILITY_NAMED_IAM\n"),
                call("CAPABILITY_AUTO_EXPAND"),
            ]
        )
        mocked_execute.assert_called_once_with(
            empty_allow=True,
            print_col=1,
            multi_select=True,
            header="lol\nPlease select the capabilities to acknowledge and proceed\nMore information: https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_CreateStack.html",
        )
        self.assertEqual(result, ["CAPABILITY_IAM"])

        mocked_execute.reset_mock()
        mocked_append.reset_mock()
        mocked_execute.return_value = ["CAPABILITY_IAM", "CAPABILITY_AUTO_EXPAND"]
        result = self.cloudformation._get_capabilities()
        mocked_append.assert_has_calls(
            [
                call("CAPABILITY_IAM\n"),
                call("CAPABILITY_NAMED_IAM\n"),
                call("CAPABILITY_AUTO_EXPAND"),
            ]
        )
        mocked_execute.assert_called_once_with(
            empty_allow=True,
            print_col=1,
            multi_select=True,
            header="\nPlease select the capabilities to acknowledge and proceed\nMore information: https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_CreateStack.html",
        )
        self.assertEqual(result, ["CAPABILITY_IAM", "CAPABILITY_AUTO_EXPAND"])

    def test_get_stack_generator(self):
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        data = [{"Stacks": [{"foo": "boo"}]}, {"Stacks": [{"hello": "world"}]}]
        generator = self.cloudformation._get_stack_generator(data)
        for item in generator:
            print(item)
        self.assertEqual(
            self.capturedOutput.getvalue(), "{'foo': 'boo'}\n{'hello': 'world'}\n"
        )
