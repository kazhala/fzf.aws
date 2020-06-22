import io
import sys
import unittest
from unittest.mock import call, patch
from fzfaws.cloudformation.helper.cloudformationargs import CloudformationArgs
from fzfaws.cloudformation import Cloudformation
from fzfaws.utils import Pyfzf


class TestCloudformationArgs(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput
        cloudformation = Cloudformation()
        self.cloudformationargs = CloudformationArgs(cloudformation)

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_constructor(self):
        self.assertEqual(self.cloudformationargs._extra_args, {})
        self.assertEqual(self.cloudformationargs.update_termination, False)
        self.assertIsInstance(self.cloudformationargs.cloudformation, Cloudformation)

    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Pyfzf, "append_fzf")
    @patch.object(CloudformationArgs, "set_creation")
    @patch.object(CloudformationArgs, "set_rollback")
    @patch.object(CloudformationArgs, "set_notification")
    @patch.object(CloudformationArgs, "set_policy")
    @patch.object(CloudformationArgs, "set_permissions")
    @patch.object(CloudformationArgs, "set_tags")
    def test_set_extra_args(
        self,
        mocked_tags,
        mocked_perm,
        mocked_policy,
        mocked_notify,
        mocked_rollback,
        mocked_create,
        mocked_append,
        mocked_execute,
    ):
        # normal test
        mocked_execute.return_value = [
            "Tags",
            "Permissions",
            "StackPolicy",
            "Notifications",
            "RollbackConfiguration",
            "CreationOption",
        ]
        self.cloudformationargs.set_extra_args()
        mocked_tags.assert_called_once_with(False)
        mocked_perm.assert_called_once_with(False)
        mocked_notify.assert_called_once_with(False)
        mocked_rollback.assert_called_once_with(False)
        mocked_policy.assert_called_once_with(False, False)
        mocked_create.assert_called_once_with(False)
        mocked_append.assert_has_calls(
            [
                call("Tags\n"),
                call("Permissions\n"),
                call("StackPolicy\n"),
                call("Notifications\n"),
                call("RollbackConfiguration\n"),
                call("CreationOption\n"),
            ]
        )

        mocked_tags.reset_mock()
        mocked_perm.reset_mock()
        mocked_notify.reset_mock()
        mocked_rollback.reset_mock()
        mocked_policy.reset_mock()
        mocked_create.reset_mock()
        mocked_append.reset_mock()
        # update test
        self.cloudformationargs.set_extra_args(update=True, search_from_root=True)
        mocked_tags.assert_called_once_with(True)
        mocked_perm.assert_called_once_with(True)
        mocked_notify.assert_called_once_with(True)
        mocked_rollback.assert_called_once_with(True)
        mocked_policy.assert_called_once_with(True, True)
        mocked_create.assert_called_once_with(True)
        mocked_append.assert_has_calls(
            [
                call("Tags\n"),
                call("Permissions\n"),
                call("StackPolicy\n"),
                call("Notifications\n"),
                call("RollbackConfiguration\n"),
                call("UpdateOption\n"),
            ]
        )

        mocked_tags.reset_mock()
        mocked_perm.reset_mock()
        mocked_notify.reset_mock()
        mocked_rollback.reset_mock()
        mocked_policy.reset_mock()
        mocked_create.reset_mock()
        mocked_append.reset_mock()
        # dryrun test
        self.cloudformationargs.set_extra_args(dryrun=True)
        mocked_tags.assert_called_once_with(False)
        mocked_perm.assert_called_once_with(False)
        mocked_notify.assert_called_once_with(False)
        mocked_rollback.assert_called_once_with(False)
        mocked_policy.assert_called_once_with(False, False)
        mocked_create.assert_called_once_with(False)
        mocked_append.assert_has_calls(
            [
                call("Tags\n"),
                call("Permissions\n"),
                call("Notifications\n"),
                call("RollbackConfiguration\n"),
            ]
        )
