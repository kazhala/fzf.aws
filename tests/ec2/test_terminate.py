import io
import sys
import unittest
from unittest.mock import patch, PropertyMock
from fzfaws.ec2.terminate_instance import terminate_instance
from fzfaws.ec2 import EC2
from fzfaws.utils import BaseSession
import boto3
from botocore.stub import Stubber


class TestEC2Terminate(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch("fzfaws.ec2.terminate_instance.get_confirmation")
    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    @patch.object(EC2, "wait")
    @patch.object(EC2, "print_instance_details")
    @patch.object(EC2, "set_ec2_instance")
    def test_terminate_instance(
        self,
        mocked_set_instance,
        mocked_detail,
        mocked_wait,
        mocked_client,
        mocked_confirmation,
    ):
        # mock the boto client
        ec2 = boto3.client("ec2")
        stubber = Stubber(ec2)
        response = {"TerminatingInstances": []}
        stubber.add_response("terminate_instances", response)
        stubber.activate()
        mocked_client.return_value = ec2
        mocked_confirmation.return_value = True

        terminate_instance(False, False, False)
        mocked_set_instance.assert_called_once()
        mocked_detail.assert_called_once()
        self.assertRegex(
            self.capturedOutput.getvalue(), r".*Instance termination initiated.*"
        )

        ec2 = boto3.client("ec2")
        stubber = Stubber(ec2)
        response = {"TerminatingInstances": []}
        stubber.add_response("terminate_instances", response)
        stubber.activate()
        mocked_client.return_value = ec2
        mocked_confirmation.return_value = True
        terminate_instance(False, False, True)
        mocked_wait.assert_called_once_with(
            "instance_terminated", "Wating for instance to be terminated ..."
        )
