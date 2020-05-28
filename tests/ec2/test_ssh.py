import os
import io
import sys
import unittest
import subprocess
from unittest.mock import patch, MagicMock
from fzfaws.ec2.ssh_instance import ssh_instance
from fzfaws.ec2 import EC2
from fzfaws.utils import FileLoader


class TestSSH(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch("fzfaws.ec2.ssh_instance.get_instance_ip")
    @patch("fzfaws.ec2.ssh_instance.construct_normal_ssh")
    @patch("fzfaws.ec2.ssh_instance.check_instance_status")
    @patch.object(EC2, "set_ec2_instance")
    def test_normal_ssh_instance(
        self,
        mocked_set_instance,
        mocked_instance_status,
        mocked_ssh_cmd,
        mocked_instance_ip,
    ):
        # basic test
        mocked_ssh_cmd.return_value = ["sleep", "0"]
        mocked_instance_ip.return_value = "11111111"
        ssh_instance()
        mocked_set_instance.assert_called_with(
            multi_select=False, header="select instance to connect"
        )
        mocked_instance_status.assert_called_with({})
        mocked_ssh_cmd.assert_called_with(
            os.path.join(os.path.expanduser("~"), ".ssh/.pem"),
            "11111111",
            "ec2-user",
            False,
        )

        # custom settings
        ssh_instance(username="kazhala", bastion=True)
        mocked_set_instance.assert_called_with(
            multi_select=False, header="select instance to connect"
        )
        mocked_instance_status.assert_called_with({})
        mocked_ssh_cmd.assert_called_with(
            os.path.join(os.path.expanduser("~"), ".ssh/.pem"),
            "11111111",
            "kazhala",
            True,
        )

    @patch("fzfaws.ec2.ssh_instance.get_instance_ip")
    @patch("fzfaws.ec2.ssh_instance.construct_tunnel_ssh")
    @patch("fzfaws.ec2.ssh_instance.check_instance_status")
    @patch.object(EC2, "set_ec2_instance")
    def test_tunnel_ssh_instance(
        self,
        mocked_set_instance,
        mocked_instance_status,
        mocked_ssh_cmd,
        mocked_instance_ip,
    ):
        # normal
        mocked_ssh_cmd.return_value = ["sleep", "0"]
        mocked_instance_ip.return_value = "11111111"
        ssh_instance(profile="root", region="us-east-1", bastion=True, tunnel=True)
        mocked_set_instance.assert_called_with(
            multi_select=False, header="select the destination instance"
        )
        mocked_instance_status.assert_called_with({})
        mocked_ssh_cmd.assert_called_with(
            os.path.join(os.path.expanduser("~"), ".ssh/.pem"),
            "11111111",
            "ec2-user",
            "11111111",
            "ec2-user",
        )

        # custom settings
        ssh_instance(tunnel="ubuntu")
        mocked_ssh_cmd.assert_called_with(
            os.path.join(os.path.expanduser("~"), ".ssh/.pem"),
            "11111111",
            "ec2-user",
            "11111111",
            "ubuntu",
        )
