import os
import io
import sys
import unittest
from unittest.mock import call, patch
from fzfaws.cloudformation.helper.paramprocessor import ParamProcessor
from fzfaws.utils import FileLoader


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
