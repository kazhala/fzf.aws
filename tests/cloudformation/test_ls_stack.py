import sys
import io
import unittest
from unittest.mock import call, patch
from fzfaws.cloudformation.ls_stack import ls_stack


class TestCloudformationLsStack(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput
        self.stack_response = {
            "StackId": "arn:aws:cloudformation:ap-southeast-2:111111:stack/dotbare-cicd/aadsfadsf",
            "StackName": "dotbare-cicd",
            "Description": "CodeBuild template for dotbare, webhook trigger from Github only on Master push",
            "RollbackConfiguration": {"RollbackTriggers": []},
            "StackStatus": "UPDATE_COMPLETE",
            "DisableRollback": False,
            "NotificationARNs": [],
            "Capabilities": ["CAPABILITY_NAMED_IAM"],
            "Tags": [
                {"Key": "Application", "Value": "mealternative"},
                {"Key": "Name", "Value": "mealternative"},
            ],
            "DriftInformation": {
                "StackDriftStatus": "IN_SYNC",
            },
        }
        self.resource_response = {
            "StackResourceDetail": {
                "StackName": "testing2",
                "StackId": "arn:aws:cloudformation:ap-southeast-2:111111:stack/testing2/adasdfasfas",
                "LogicalResourceId": "EC2InstanceSecurityGroup",
                "PhysicalResourceId": "testing2-EC2InstanceSecurityGroup-114ROX9C6WM6Y",
                "ResourceType": "AWS::EC2::SecurityGroup",
                "LastUpdatedTimestamp": "2020-07-03 01:45:54.164000+00:00",
                "ResourceStatus": "UPDATE_COMPLETE",
                "Metadata": "{}",
                "DriftInformation": {"StackResourceDriftStatus": "IN_SYNC"},
            }
        }

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch("fzfaws.cloudformation.ls_stack.Cloudformation")
    def test_ls_resource(self, MockedCloudformation):
        cloudformation = MockedCloudformation()
        cloudformation.stack_details = self.stack_response
        cloudformation.stack_name = "testing2"
        cloudformation.client.describe_stack_resource.return_value = (
            self.resource_response
        )
        cloudformation.get_stack_resources.return_value = [
            "EC2InstanceSecurityGroup",
            "fooboo",
        ]
        ls_stack(resource=True)
        cloudformation.set_stack.assert_called_once()
        cloudformation.get_stack_resources.assert_called_once()
        self.assertRegex(self.capturedOutput.getvalue(), r'"StackName": "testing2"')
        self.assertRegex(
            self.capturedOutput.getvalue(),
            r'"LogicalResourceId": "EC2InstanceSecurityGroup"',
        )
        cloudformation.client.describe_stack_resource.assert_has_calls(
            [
                call(
                    StackName="testing2", LogicalResourceId="EC2InstanceSecurityGroup"
                ),
                call(StackName="testing2", LogicalResourceId="fooboo"),
            ]
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        cloudformation.get_stack_resources.return_value = [
            "EC2InstanceSecurityGroup",
        ]
        ls_stack(resource=True, name=True, arn=True, resource_type=True)
        self.assertNotRegex(self.capturedOutput.getvalue(), r'"StackName": "testing2"')
        self.assertNotRegex(
            self.capturedOutput.getvalue(),
            r'"LogicalResourceId": "EC2InstanceSecurityGroup"',
        )
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "EC2InstanceSecurityGroup\nAWS::EC2::SecurityGroup\n",
        )

    @patch("fzfaws.cloudformation.ls_stack.Cloudformation")
    def test_ls_stack(self, MockedCloudformation):
        cloudformation = MockedCloudformation()
        cloudformation.stack_name = "dotbare-cicd"
        cloudformation.stack_details = self.stack_response
        ls_stack(profile="master", region="us-east-1")
        MockedCloudformation.assert_called_with("master", "us-east-1")
        self.assertRegex(self.capturedOutput.getvalue(), r'"StackName": "dotbare-cicd"')
        self.assertRegex(
            self.capturedOutput.getvalue(),
            r'"StackId": "arn:aws:cloudformation:ap-southeast-2:111111:stack/dotbare-cicd/aadsfadsf"',
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ls_stack(name=True, arn=True, tag=True, resource_type=True)
        self.assertNotRegex(
            self.capturedOutput.getvalue(), r'"StackName": "dotbare-cicd"'
        )
        self.assertNotRegex(
            self.capturedOutput.getvalue(),
            r'"StackId": "arn:aws:cloudformation:ap-southeast-2:111111:stack/dotbare-cicd/aadsfadsf"',
        )
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "dotbare-cicd\narn:aws:cloudformation:ap-southeast-2:111111:stack/dotbare-cicd/aadsfadsf\n[{'Key': 'Application', 'Value': 'mealternative'}, {'Key': 'Name', 'Value': 'mealternative'}]\n",
        )
