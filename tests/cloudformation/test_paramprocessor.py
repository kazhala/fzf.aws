from fzfaws.route53.route53 import Route53
from fzfaws.ec2.ec2 import EC2
from fzfaws.utils.session import BaseSession
from fzfaws.utils.pyfzf import Pyfzf
import os
import io
import sys
import unittest
from unittest.mock import PropertyMock, call, patch
from fzfaws.cloudformation.helper.paramprocessor import ParamProcessor
from fzfaws.utils import FileLoader
import boto3
from botocore.stub import Stubber
import json


class TestCloudformationParams(unittest.TestCase):
    def setUp(self):
        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../data/cloudformation_template.yaml",
        )
        fileloader = FileLoader(path=data_path)
        params = fileloader.process_yaml_file()["dictBody"].get("Parameters", {})
        self.paramprocessor = ParamProcessor(params=params)
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_constructor(self):
        self.assertEqual(self.paramprocessor.ec2.profile, None)
        self.assertEqual(self.paramprocessor.ec2.region, None)
        self.assertEqual(self.paramprocessor.route53.profile, None)
        self.assertEqual(self.paramprocessor.route53.region, None)
        self.assertIsInstance(self.paramprocessor.params, dict)
        self.assertEqual(self.paramprocessor.original_params, [])
        self.assertEqual(self.paramprocessor.processed_params, [])

        paramprocessor = ParamProcessor(profile="root", region="us-east-1")
        self.assertEqual(paramprocessor.ec2.profile, "root")
        self.assertEqual(paramprocessor.ec2.region, "us-east-1")
        self.assertEqual(paramprocessor.route53.profile, "root")
        self.assertEqual(paramprocessor.route53.region, "us-east-1")
        self.assertEqual(paramprocessor.params, {})
        self.assertEqual(paramprocessor.processed_params, [])
        self.assertEqual(paramprocessor.original_params, [])

    @patch.object(ParamProcessor, "_get_user_input")
    def test_process_stack_params(self, mocked_input):
        mocked_input.return_value = "111111"

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        self.paramprocessor.process_stack_params()
        self.assertEqual(
            self.paramprocessor.processed_params,
            [
                {"ParameterKey": "InstanceRole", "ParameterValue": "111111"},
                {"ParameterKey": "LatestAmiId", "ParameterValue": "111111"},
                {"ParameterKey": "SubnetId", "ParameterValue": "111111"},
                {"ParameterKey": "SecurityGroups", "ParameterValue": "111111"},
                {"ParameterKey": "KeyName", "ParameterValue": "111111"},
                {"ParameterKey": "WebServer", "ParameterValue": "111111"},
                {"ParameterKey": "InstanceType", "ParameterValue": "111111"},
            ],
        )
        self.assertRegex(
            self.capturedOutput.getvalue(),
            r"Description: The subnet this instance should be deployed to",
        )
        self.assertRegex(
            self.capturedOutput.getvalue(),
            r"ConstraintDescription: must be the name of an existing EC2 KeyPair",
        )
        self.assertRegex(
            self.capturedOutput.getvalue(), r"ParameterValue: 111111",
        )
        mocked_input.assert_called_with(
            "InstanceType",
            "String",
            "Description: EC2 instance type\nConstraintDescription: must be a valid EC2 instance type\nType: String\n",
            "Default",
            "t2.micro",
        )
        mocked_input.assert_has_calls(
            [
                call(
                    "InstanceRole",
                    "String",
                    "Description: Name of the instance role, skip the value if don't have one\nType: String\n",
                )
            ]
        )

        mocked_input.return_value = "222222"
        self.paramprocessor.processed_params = []
        self.paramprocessor.original_params = [
            {"ParameterKey": "KeyName", "ParameterValue": "fooboo"},
            {"ParameterKey": "SecurityGroups", "ParameterValue": "sg-111111",},
            {"ParameterKey": "WebServer", "ParameterValue": "No"},
            {
                "ParameterKey": "LatestAmiId",
                "ParameterValue": "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2",
                "ResolvedValue": "ami-08fdde86b93accf1c",
            },
            {"ParameterKey": "InstanceRole", "ParameterValue": ""},
            {"ParameterKey": "SubnetId", "ParameterValue": "subnet-111111"},
            {"ParameterKey": "InstanceType", "ParameterValue": "t2.micro"},
        ]
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        self.paramprocessor.process_stack_params()
        self.assertEqual(
            self.paramprocessor.processed_params,
            [
                {"ParameterKey": "InstanceRole", "ParameterValue": "222222"},
                {"ParameterKey": "LatestAmiId", "ParameterValue": "222222"},
                {"ParameterKey": "SubnetId", "ParameterValue": "222222"},
                {"ParameterKey": "SecurityGroups", "ParameterValue": "222222"},
                {"ParameterKey": "KeyName", "ParameterValue": "222222"},
                {"ParameterKey": "WebServer", "ParameterValue": "222222"},
                {"ParameterKey": "InstanceType", "ParameterValue": "222222"},
            ],
        )
        self.assertRegex(
            self.capturedOutput.getvalue(),
            r"Description: The subnet this instance should be deployed to",
        )
        self.assertRegex(
            self.capturedOutput.getvalue(),
            r"ConstraintDescription: must be the name of an existing EC2 KeyPair",
        )
        self.assertRegex(
            self.capturedOutput.getvalue(), r"ParameterValue: 222222",
        )
        mocked_input.assert_called_with(
            "InstanceType",
            "String",
            "Description: EC2 instance type\nConstraintDescription: must be a valid EC2 instance type\nType: String\n",
            "Original",
            "t2.micro",
        )

        mocked_input.return_value = ["111111", "222222"]
        self.paramprocessor.processed_params = []
        self.paramprocessor.original_params = []
        self.paramprocessor.process_stack_params()
        self.assertEqual(
            self.paramprocessor.processed_params,
            [
                {"ParameterKey": "InstanceRole", "ParameterValue": "111111,222222",},
                {"ParameterKey": "LatestAmiId", "ParameterValue": "111111,222222"},
                {"ParameterKey": "SubnetId", "ParameterValue": "111111,222222"},
                {"ParameterKey": "SecurityGroups", "ParameterValue": "111111,222222"},
                {"ParameterKey": "KeyName", "ParameterValue": "111111,222222"},
                {"ParameterKey": "WebServer", "ParameterValue": "111111,222222"},
                {"ParameterKey": "InstanceType", "ParameterValue": "111111,222222"},
            ],
        )

    @patch("builtins.input")
    @patch.object(ParamProcessor, "_get_list_param_value")
    @patch.object(ParamProcessor, "_get_selected_param_value")
    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Pyfzf, "append_fzf")
    @patch.object(ParamProcessor, "_print_parameter_key")
    def test_get_user_input(
        self,
        mocked_print,
        mocked_append,
        mocked_execute,
        mocked_select,
        mocked_list,
        mocked_input,
    ):

        # normal var with no default value test
        mocked_input.return_value = "111111"
        result = self.paramprocessor._get_user_input(
            "InstanceRole", "String", "foo boo"
        )
        mocked_input.assert_called_once_with("InstanceRole: ")
        mocked_print.assert_not_called()
        mocked_append.assert_not_called()
        mocked_execute.assert_not_called()
        mocked_select.assert_not_called()
        mocked_list.assert_not_called()
        self.assertEqual(result, "111111")

        mocked_input.reset_mock()
        mocked_print.reset_mock()
        mocked_append.reset_mock()
        mocked_execute.reset_mock()
        mocked_select.reset_mock()
        mocked_list.reset_mock()
        # test allowed_value
        mocked_print.return_value = ""
        mocked_execute.return_value = "111111"
        result = self.paramprocessor._get_user_input(
            "WebServer", "String", "foo boo", "Default", "No"
        )
        mocked_print.assert_called_with("WebServer", "Default", "No")
        mocked_append.assert_has_calls([call("Yes\n"), call("No\n")])
        mocked_execute.assert_called_once_with(
            empty_allow=True, print_col=1, header="foo boo"
        )
        mocked_select.assert_not_called()
        mocked_list.assert_not_called()
        mocked_input.assert_not_called()
        self.assertEqual(result, "111111")

        mocked_input.reset_mock()
        mocked_print.reset_mock()
        mocked_append.reset_mock()
        mocked_execute.reset_mock()
        mocked_select.reset_mock()
        mocked_list.reset_mock()
        # test select aws value
        mocked_print.return_value = ""
        mocked_select.return_value = "111111"
        result = self.paramprocessor._get_user_input(
            "KeyName", "AWS::EC2::KeyPair::KeyName", "foo boo", "Original", "lol"
        )
        mocked_print.assert_called_with("KeyName", "Original", "lol")
        mocked_select.assert_called_once_with("AWS::EC2::KeyPair::KeyName", "foo boo")
        mocked_append.assert_not_called()
        mocked_execute.assert_not_called()
        mocked_list.assert_not_called()
        mocked_input.assert_not_called()
        self.assertEqual(result, "111111")

        mocked_input.reset_mock()
        mocked_print.reset_mock()
        mocked_append.reset_mock()
        mocked_execute.reset_mock()
        mocked_select.reset_mock()
        mocked_list.reset_mock()
        # test list aws value
        mocked_list.return_value = "111111"
        result = self.paramprocessor._get_user_input(
            "SecurityGroups", "List<AWS::EC2::SecurityGroup::Id>", "foo boo"
        )
        mocked_print.assert_called_with("SecurityGroups", None, None)
        mocked_list.assert_called_once_with(
            "List<AWS::EC2::SecurityGroup::Id>", "foo boo"
        )
        mocked_append.assert_not_called()
        mocked_execute.assert_not_called()
        mocked_select.assert_not_called()
        mocked_input.assert_not_called()
        self.assertEqual(result, "111111")

    def test_print_parameter_key(self):
        result = self.paramprocessor._print_parameter_key(
            "SecurityGroups", "Default", "111111"
        )
        self.assertEqual(result, "Choose a value for SecurityGroups(Default: 111111)")

        result = self.paramprocessor._print_parameter_key(
            "SecurityGroups", "Original", "111111"
        )
        self.assertEqual(result, "Choose a value for SecurityGroups(Original: 111111)")

        result = self.paramprocessor._print_parameter_key("SecurityGroups")
        self.assertEqual(result, "Choose a value for SecurityGroups")

    @patch.object(Route53, "set_zone_id")
    @patch.object(EC2, "get_security_groups")
    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Pyfzf, "process_list")
    def test_get_selected_param_value(
        self, mocked_process, mocked_execute, mocked_client, mocked_sg, mocked_zone,
    ):
        mocked_execute.return_value = "111111"

        # keypair test for normal client test
        keypair_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/ec2_keypair.json"
        )
        with open(keypair_path, "r") as file:
            keypair_response = json.load(file)
        ec2 = boto3.client("ec2")
        stubber = Stubber(ec2)
        stubber.add_response("describe_key_pairs", keypair_response)
        stubber.activate()
        mocked_client.return_value = ec2
        result = self.paramprocessor._get_selected_param_value(
            "AWS::EC2::KeyPair::KeyName", "foo boo"
        )
        mocked_process.assert_called_once_with(
            [
                {
                    "KeyPairId": "key-111111",
                    "KeyFingerprint": "asdfasfsadfasdfafasf",
                    "KeyName": "ap-southeast-foo-boo",
                    "Tags": [],
                }
            ],
            "KeyName",
            empty_allow=True,
        )
        mocked_execute.assert_called_once_with(empty_allow=True, header="foo boo")
        mocked_sg.assert_not_called()
        self.assertEqual(result, "111111")

        # security group test for ec2 method
        mocked_execute.reset_mock()
        mocked_process.reset_mock()
        mocked_sg.return_value = "111111"
        result = self.paramprocessor._get_selected_param_value(
            "AWS::EC2::SecurityGroup::Id", "foo boo"
        )
        mocked_sg.assert_called_once_with(header="foo boo")
        mocked_execute.assert_not_called()
        mocked_process.assert_not_called()
        self.assertEqual(result, "111111")

        # route53 zone test
        result = self.paramprocessor._get_selected_param_value(
            "AWS::Route53::HostedZone::Id", "foo boo"
        )
        mocked_execute.assert_not_called()
        mocked_process.assert_not_called()
        mocked_zone.assert_called_once()
        self.assertEqual(result, "")

    @patch.object(Route53, "set_zone_id")
    @patch.object(EC2, "get_security_groups")
    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    @patch.object(Pyfzf, "process_list")
    @patch.object(Pyfzf, "execute_fzf")
    def test_get_list_param_value(
        self, mocked_execute, mocked_process, mocked_client, mocked_sg, mocked_zone
    ):

        mocked_execute.return_value = ["111111", "222222"]
        # az list test for normal client test
        az_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/ec2_az.json"
        )
        with open(az_path, "r") as file:
            az_response = json.load(file)
        ec2 = boto3.client("ec2")
        stubber = Stubber(ec2)
        stubber.add_response("describe_availability_zones", az_response)
        stubber.activate()
        mocked_client.return_value = ec2
        result = self.paramprocessor._get_list_param_value(
            "List<AWS::EC2::AvailabilityZone::Name>", "foo boo"
        )
        mocked_process.assert_called_once_with(
            az_response["AvailabilityZones"], "ZoneName", empty_allow=True,
        )
        mocked_execute.assert_called_once_with(
            multi_select=True, empty_allow=True, header="foo boo"
        )
        mocked_sg.assert_not_called()
        self.assertEqual(result, ["111111", "222222"])

        # sg test for ec2 method
        mocked_process.reset_mock()
        mocked_execute.reset_mock()
        mocked_sg.return_value = ["111111", "222222"]
        result = self.paramprocessor._get_list_param_value(
            "List<AWS::EC2::SecurityGroup::GroupName>", "foo boo"
        )
        mocked_sg.assert_called_once_with(
            multi_select=True, return_attr="name", header="foo boo"
        )
        self.assertEqual(result, ["111111", "222222"])

        # zone test for route53 method
        result = self.paramprocessor._get_list_param_value(
            "List<AWS::Route53::HostedZone::Id>", "foo boo"
        )
        mocked_zone.assert_called_once()
        self.assertEqual(result, [""])
