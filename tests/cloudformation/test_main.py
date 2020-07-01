import io
import sys
import unittest
from unittest.mock import patch
from fzfaws.cloudformation.main import cloudformation


class TestCloudformationMain(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_help(self):
        self.assertRaises(SystemExit, cloudformation, ["create", "-h"])
        self.assertRaises(SystemExit, cloudformation, ["update", "-h"])
        self.assertRaises(SystemExit, cloudformation, ["delete", "-h"])
        self.assertRaises(SystemExit, cloudformation, ["ls", "-h"])
        self.assertRaises(SystemExit, cloudformation, ["validate", "-h"])
        self.assertRaises(SystemExit, cloudformation, ["drift", "-h"])
        self.assertRaises(SystemExit, cloudformation, ["changeset", "-h"])

    @patch("fzfaws.cloudformation.main.create_stack")
    def test_create_stack(self, mocked_create):
        cloudformation(["create"])
        mocked_create.assert_called_with(
            False, False, False, False, False, False, None, False
        )

        cloudformation(
            ["create", "-P", "-R", "-l", "hello.yaml", "-b", "kazhala-lol/", "-w", "-v"]
        )
        mocked_create.assert_called_with(
            True, True, "hello.yaml", False, True, False, "kazhala-lol/", True
        )

    @patch("fzfaws.cloudformation.main.update_stack")
    def test_update_stack(self, mocked_update):
        cloudformation(["update"])
        mocked_update.assert_called_with(
            False, False, False, False, False, False, False, None, False
        )

        cloudformation(["update", "-P", "root", "-R", "us-east-1", "-l", "-x", "-E"])
        mocked_update.assert_called_with(
            "root", "us-east-1", True, True, False, False, True, None, False
        )

    @patch("fzfaws.cloudformation.main.delete_stack")
    def test_delete_stack(self, mocked_delete):
        cloudformation(["delete"])
        mocked_delete.assert_called_with(False, False, False, False)

        cloudformation(["delete", "-P", "-w", "-i", "arn:111111"])
        mocked_delete.assert_called_with(True, False, True, "arn:111111")

    @patch("fzfaws.cloudformation.main.ls_stack")
    def test_ls_stack(self, mocked_ls):
        cloudformation(["ls"])
        mocked_ls.assert_called_with(False, False, False)

        cloudformation(["ls", "-R", "--resource"])
        mocked_ls.assert_called_with(False, True, True)

    @patch("fzfaws.cloudformation.main.drift_stack")
    def test_drift_stack(self, mocked_drift):
        cloudformation(["drift"])
        mocked_drift.assert_called_with(False, False, False, False)

        cloudformation(["drift", "-i", "-s"])
        mocked_drift.assert_called_with(False, False, True, True)

    @patch("fzfaws.cloudformation.main.changeset_stack")
    def test_changeset_stack(self, mocked_change):
        cloudformation(["changeset"])
        mocked_change.assert_called_with(
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
            None,
            False,
        )

        cloudformation(
            [
                "changeset",
                "-b",
                "kazhala-lol/hello.yaml",
                "-v",
                "111111",
                "-w",
                "-x",
                "-E",
            ]
        )
        mocked_change.assert_called_with(
            False,
            False,
            True,
            False,
            False,
            True,
            False,
            False,
            False,
            True,
            "kazhala-lol/hello.yaml",
            "111111",
        )

        cloudformation(["changeset", "-i"])
        mocked_change.assert_called_with(
            False,
            False,
            False,
            False,
            False,
            False,
            True,
            False,
            False,
            False,
            None,
            False,
        )

    @patch("fzfaws.cloudformation.main.validate_stack")
    def test_validate_stack(self, mocked_validate):
        cloudformation(["validate"])
        mocked_validate.assert_called_with(
            False, False, False, False, None, False,
        )

        cloudformation(["validate", "-P", "root", "-R", "us-east-1", "-r", "-l"])
        mocked_validate.assert_called_with(
            "root", "us-east-1", True, True, None, False,
        )

        cloudformation(["validate", "-b", "kazhala-lol/", "-v"])
        mocked_validate.assert_called_with(
            False, False, False, False, "kazhala-lol/", True,
        )
