import io
import sys
import unittest
from unittest.mock import patch, PropertyMock
from fzfaws.ec2.reboot_instance import reboot_instance
from fzfaws.ec2 import EC2
from fzfaws.utils import BaseSession
import boto3
from botocore.stub import Stubber


class TestEC2Reboot(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch("fzfaws.ec2.reboot_instance.get_confirmation")
    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    @patch.object(EC2, "print_instance_details")
    @patch.object(EC2, "set_ec2_instance")
    def test_reboot_instance(
        self, mocked_set_instance, mocked_detail, mocked_client, mocked_confirmation
    ):

        # client mock
        ec2 = boto3.client("ec2")
        stubber = Stubber(ec2)
        response = {"ResponseMetadata": []}
        stubber.add_response("reboot_instances", response)
        stubber.activate()
        mocked_client.return_value = ec2
        mocked_confirmation.return_value = True

        reboot_instance(False, False)
        mocked_set_instance.assert_called_once()
        mocked_detail.assert_called_once()
        self.assertRegex(
            self.capturedOutput.getvalue(), r".*Instance will remain in running state.*"
        )
