import os
import io
import sys
import unittest
from unittest.mock import patch
from fzfaws.ec2.ssh_instance import ssh_instance, check_instance_status, get_instance_ip
from fzfaws.ec2 import EC2
from fzfaws.utils.exceptions import EC2Error


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

    def test_check_instance_status(self):
        self.assertRaises(
            EC2Error,
            check_instance_status,
            {"Status": "stopped", "InstanceId": "11111111"},
        )
        self.assertRaises(
            EC2Error,
            check_instance_status,
            {"Status": "pending", "InstanceId": "11111111"},
        )
        check_instance_status({"Status": "running", "InstanceId": "11111111"})

    def test_get_instance_ip(self):
        self.assertRaises(EC2Error, get_instance_ip, {})
        result = get_instance_ip({"PublicDnsName": "11111111"})
        self.assertEqual(result, "11111111")

        result = get_instance_ip({"PublicIpAddress": "11111111"})
        self.assertEqual(result, "11111111")

        result = get_instance_ip({"PrivateIpAddress": "11111111"})
        self.assertEqual(result, "11111111")

        result = get_instance_ip(
            {
                "PublicDnsName": "11111111",
                "PublicIpAddress": "22222222",
                "PrivateIpAddress": "3333333",
            },
            "dns",
        )
        self.assertEqual(result, "11111111")

        result = get_instance_ip(
            {
                "PublicDnsName": "11111111",
                "PublicIpAddress": "22222222",
                "PrivateIpAddress": "3333333",
            },
            "public",
        )
        self.assertEqual(result, "22222222")

        result = get_instance_ip(
            {
                "PublicDnsName": "11111111",
                "PublicIpAddress": "22222222",
                "PrivateIpAddress": "3333333",
            },
            "private",
        )
        self.assertEqual(result, "3333333")
