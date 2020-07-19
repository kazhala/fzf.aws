import io
import sys
import unittest
from unittest.mock import patch, PropertyMock
from fzfaws.ec2.stop_instance import stop_instance
from fzfaws.ec2 import EC2
from fzfaws.utils import BaseSession
from botocore.stub import Stubber
import boto3


class TestEC2Stop(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch("fzfaws.ec2.stop_instance.get_confirmation")
    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    @patch.object(EC2, "print_instance_details")
    @patch.object(EC2, "wait")
    @patch.object(EC2, "set_ec2_instance")
    def test_stop_instance(
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
        response = {"StoppingInstances": []}
        stubber.add_response("stop_instances", response)
        stubber.activate()
        mocked_client.return_value = ec2
        mocked_confirmation.return_value = True

        stop_instance()
        mocked_detail.assert_called_once()
        mocked_set_instance.assert_called_once()
        mocked_wait.assert_not_called()
        self.assertRegex(self.capturedOutput.getvalue(), r".*Instance stop initiated.*")

        # mock what needed to be mocked
        ec2 = boto3.client("ec2")
        stubber = Stubber(ec2)
        response = {"StoppingInstances": []}
        stubber.add_response("stop_instances", response)
        stubber.activate()
        mocked_client.return_value = ec2
        mocked_confirmation.return_value = True
        mocked_detail.reset_mock()
        mocked_set_instance.reset_mock()

        stop_instance(False, False, True, True)
        mocked_detail.assert_called_once()
        mocked_set_instance.assert_called_once()
        mocked_wait.assert_called_once()
        self.assertRegex(self.capturedOutput.getvalue(), r".*Instance stop initiated.*")
        self.assertRegex(self.capturedOutput.getvalue(), r".*Instance stopped.*")
