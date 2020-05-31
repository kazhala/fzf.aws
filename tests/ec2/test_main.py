import unittest
from unittest.mock import patch
from fzfaws.ec2.main import ec2


class TestEC2Main(unittest.TestCase):
    @patch("fzfaws.ec2.main.ssh_instance")
    def test_ec2_ssh(self, mocked_ssh):
        ec2(["ssh"])
        mocked_ssh.assert_called_with(False, False, False, "ec2-user", False, "")

        ec2(["ssh", "-p", ".", "-u", "ubuntu"])
        mocked_ssh.assert_called_with(False, False, False, "ubuntu", False, ".")

        ec2(["ssh", "-P", "root", "-R", "us-east-1", "-A", "-t"])
        mocked_ssh.assert_called_with("root", "us-east-1", True, "ec2-user", True, "")

    @patch("fzfaws.ec2.main.start_instance")
    def test_ec2_start(self, mocked_start):
        ec2(["start"])
        mocked_start.assert_called_with(False, False, False, False)

        ec2(["start", "-P", "-R", "-w", "-W"])
        mocked_start.assert_called_with(True, True, True, True)

    @patch("fzfaws.ec2.main.stop_instance")
    def test_ec2_stop(self, mocked_stop):
        ec2(["stop"])
        mocked_stop.assert_called_with(False, False, False, False)

        ec2(["stop", "-P", "root", "-R", "-H", "-w"])
        mocked_stop.assert_called_with("root", True, True, True)

    @patch("fzfaws.ec2.main.reboot_instance")
    def test_ec2_reboot(self, mocked_reboot):
        ec2(["reboot"])
        mocked_reboot.assert_called_with(False, False)

        ec2(["reboot", "-P", "-R"])
        mocked_reboot.assert_called_with(True, True)

    @patch("fzfaws.ec2.main.terminate_instance")
    def test_terminate_instance(self, mocked_terminate):
        ec2(["terminate"])
        mocked_terminate.assert_called_with(False, False, False)

        ec2(["terminate", "-R", "us-east-1", "-w"])
        mocked_terminate.assert_called_with(False, "us-east-1", True)

    @patch("fzfaws.ec2.main.ls_instance")
    def test_ls_instance(self, mocked_ls):
        ec2(["ls"])
        mocked_ls.assert_called_with(
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
        )

        ec2(["ls", "-P"])
        mocked_ls.assert_called_with(
            True,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
        )
