import io
import sys
import unittest
from unittest.mock import patch, PropertyMock
from fzfaws.ec2.start_instance import start_instance
from fzfaws.ec2 import EC2
from botocore.stub import Stubber
import boto3
from fzfaws.utils import BaseSession


class TestEC2Start(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch("fzfaws.ec2.start_instance.get_confirmation")
    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    @patch.object(EC2, "print_instance_details")
    @patch.object(EC2, "wait")
    @patch.object(EC2, "set_ec2_instance")
    def test_start_instance(
        self,
        mocked_set_instance,
        mocked_wait,
        mocked_detail,
        mocked_client,
        mocked_confirmation,
    ):
        # mock what needed to be mocked
        ec2 = boto3.client("ec2")
        stubber = Stubber(ec2)
        response = {"StartingInstances": []}
        stubber.add_response("start_instances", response)
        stubber.activate()
        mocked_client.return_value = ec2
        mocked_confirmation.return_value = True

        start_instance(False, False, False, False)
        mocked_set_instance.assert_called_once()
        mocked_detail.assert_called_once()
        self.assertRegex(
            self.capturedOutput.getvalue(), r".*Instance start initiated.*",
        )
        self.assertRegex(
            self.capturedOutput.getvalue(), r"Starting instance now.*",
        )

        # remock
        ec2 = boto3.client("ec2")
        stubber = Stubber(ec2)
        response = {"StartingInstances": []}
        stubber.add_response("start_instances", response)
        stubber.activate()
        mocked_client.return_value = ec2
        mocked_confirmation.return_value = True
        mocked_set_instance.reset_mock()
        mocked_detail.reset_mock()

        start_instance("root", "us-east-1", False, True)
        mocked_set_instance.assert_called_once()
        mocked_detail.assert_called_once()
        self.assertRegex(
            self.capturedOutput.getvalue(), r"Starting instance now.*",
        )
        self.assertRegex(
            self.capturedOutput.getvalue(), r".*Instance start initiated.*",
        )
        self.assertRegex(self.capturedOutput.getvalue(), r".*Instance is ready")
