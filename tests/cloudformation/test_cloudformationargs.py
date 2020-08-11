import io
import json
import os
import sys
import unittest
from unittest.mock import ANY, call, patch

from fzfaws.cloudformation import Cloudformation
from fzfaws.cloudformation.helper.cloudformationargs import CloudformationArgs
from fzfaws.cloudwatch import Cloudwatch
from fzfaws.iam.iam import IAM
from fzfaws.sns import SNS
from fzfaws.utils import Pyfzf, prompt_style


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
        self.assertEqual(self.cloudformationargs.update_termination, None)
        self.assertIsInstance(self.cloudformationargs.cloudformation, Cloudformation)

    @patch("fzfaws.cloudformation.helper.cloudformationargs.prompt")
    @patch.object(CloudformationArgs, "_set_creation")
    @patch.object(CloudformationArgs, "_set_rollback")
    @patch.object(CloudformationArgs, "_set_notification")
    @patch.object(CloudformationArgs, "_set_policy")
    @patch.object(CloudformationArgs, "_set_permissions")
    @patch.object(CloudformationArgs, "_set_tags")
    def test_set_extra_args(
        self,
        mocked_tags,
        mocked_perm,
        mocked_policy,
        mocked_notify,
        mocked_rollback,
        mocked_create,
        mocked_prompt,
    ):
        # normal test
        mocked_prompt.return_value = {
            "answer": [
                "Tags",
                "Permissions",
                "StackPolicy",
                "Notifications",
                "RollbackConfiguration",
                "CreationOption",
            ]
        }
        self.cloudformationargs.set_extra_args()
        mocked_tags.assert_called_once_with(False)
        mocked_perm.assert_called_once_with(False)
        mocked_notify.assert_called_once_with(False)
        mocked_rollback.assert_called_once_with(False)
        mocked_policy.assert_called_once_with(False, False)
        mocked_create.assert_called_once_with()
        mocked_prompt.assert_called_once_with(
            [
                {
                    "type": "checkbox",
                    "name": "answer",
                    "message": "Select options to configure",
                    "choices": [
                        {"name": "Tags"},
                        {"name": "Permissions"},
                        {"name": "Notifications"},
                        {"name": "RollbackConfiguration"},
                        {"name": "StackPolicy"},
                        {"name": "CreationOption"},
                    ],
                }
            ],
            style=prompt_style,
        )

        mocked_tags.reset_mock()
        mocked_perm.reset_mock()
        mocked_notify.reset_mock()
        mocked_rollback.reset_mock()
        mocked_policy.reset_mock()
        mocked_create.reset_mock()
        mocked_prompt.reset_mock()
        # update test
        self.cloudformationargs.set_extra_args(update=True, search_from_root=True)
        mocked_tags.assert_called_once_with(True)
        mocked_perm.assert_called_once_with(True)
        mocked_notify.assert_called_once_with(True)
        mocked_rollback.assert_called_once_with(True)
        mocked_policy.assert_called_once_with(True, True)
        mocked_create.assert_called_once_with()
        mocked_prompt.assert_called_once_with(
            [
                {
                    "type": "checkbox",
                    "name": "answer",
                    "message": "Select options to configure",
                    "choices": [
                        {"name": "Tags"},
                        {"name": "Permissions"},
                        {"name": "Notifications"},
                        {"name": "RollbackConfiguration"},
                        {"name": "StackPolicy"},
                    ],
                }
            ],
            style=prompt_style,
        )

        mocked_tags.reset_mock()
        mocked_perm.reset_mock()
        mocked_notify.reset_mock()
        mocked_rollback.reset_mock()
        mocked_policy.reset_mock()
        mocked_create.reset_mock()
        mocked_prompt.reset_mock()
        # dryrun test
        self.cloudformationargs.set_extra_args(dryrun=True)
        mocked_tags.assert_called_once_with(False)
        mocked_perm.assert_called_once_with(False)
        mocked_notify.assert_called_once_with(False)
        mocked_rollback.assert_called_once_with(False)
        mocked_policy.assert_called_once_with(False, False)
        mocked_create.assert_called_once_with()
        mocked_prompt.assert_called_once_with(
            [
                {
                    "type": "checkbox",
                    "name": "answer",
                    "message": "Select options to configure",
                    "choices": [
                        {"name": "Tags"},
                        {"name": "Permissions"},
                        {"name": "Notifications"},
                        {"name": "RollbackConfiguration"},
                    ],
                }
            ],
            style=prompt_style,
        )

        mocked_prompt.return_value = {}
        self.assertRaises(KeyboardInterrupt, self.cloudformationargs.set_extra_args)

    @patch("fzfaws.cloudformation.helper.cloudformationargs.prompt")
    def test__set_creation(self, mocked_prompt):
        self.cloudformationargs._extra_args = {}

        # normal test
        mocked_prompt.return_value = {
            "selected_options": [
                "RollbackOnFailure",
                "TimeoutInMinutes",
                "EnableTerminationProtection",
            ],
            "rollback": "True",
            "timeout": "5",
            "termination": "False",
        }
        self.cloudformationargs._set_creation()
        self.assertEqual(
            self.cloudformationargs._extra_args,
            {
                "OnFailure": "ROLLBACK",
                "TimeoutInMinutes": 5,
                "EnableTerminationProtection": False,
            },
        )
        mocked_prompt.assert_called_once_with(
            [
                {
                    "type": "checkbox",
                    "name": "selected_options",
                    "message": "Select creation options to configure",
                    "choices": [
                        {"name": "RollbackOnFailure"},
                        {"name": "TimeoutInMinutes"},
                        {"name": "EnableTerminationProtection"},
                    ],
                },
                {
                    "type": "rawlist",
                    "name": "rollback",
                    "message": "Roll back on failure?",
                    "choices": ["True", "False"],
                    "when": ANY,
                },
                {
                    "type": "input",
                    "name": "timeout",
                    "message": "Specify number of minutes before timeout",
                    "when": ANY,
                },
                {
                    "type": "rawlist",
                    "name": "termination",
                    "message": "Enable termination protection?",
                    "choices": ["True", "False"],
                    "when": ANY,
                },
            ],
            style=prompt_style,
        )

        mocked_prompt.return_value = {}
        self.assertRaises(KeyboardInterrupt, self.cloudformationargs._set_creation)

    @patch("fzfaws.cloudformation.helper.cloudformationargs.prompt")
    @patch("fzfaws.cloudformation.helper.cloudformationargs.Cloudwatch")
    def test__set_rollback(self, MockedCloudwatch, mocked_prompt):
        self.cloudformationargs._extra_args = {}

        # normal test
        cloudwatch = MockedCloudwatch.return_value
        cloudwatch.arns = ["hello"]
        mocked_prompt.return_value = {"answer": "5"}
        self.cloudformationargs._set_rollback(update=False)
        cloudwatch.set_arns.assert_called_once_with(
            empty_allow=True,
            header="select cloudwatch alarms to monitor the stack",
            multi_select=True,
        )
        mocked_prompt.assert_called_once_with(
            [{"type": "input", "message": "MonitoringTimeInMinutes", "name": "answer"}],
            style=prompt_style,
        )
        self.assertEqual(
            self.cloudformationargs._extra_args,
            {
                "RollbackConfiguration": {
                    "RollbackTriggers": [
                        {"Arn": "hello", "Type": "AWS::CloudWatch::Alarm"}
                    ],
                    "MonitoringTimeInMinutes": 5,
                }
            },
        )

        cloudwatch.set_arns.reset_mock()
        mocked_prompt.reset_mock()
        # update test
        self.cloudformationargs.cloudformation.stack_details = {
            "RollbackConfiguration": {
                "RollbackTriggers": "111111",
                "MonitoringTimeInMinutes": 1,
            }
        }
        self.cloudformationargs._set_rollback(update=True)
        cloudwatch.set_arns.assert_called_once_with(
            empty_allow=True,
            header="select cloudwatch alarms to monitor the stack\nOriginal value: 111111",
            multi_select=True,
        )
        mocked_prompt.assert_called_once_with(
            [
                {
                    "type": "input",
                    "message": "MonitoringTimeInMinutes",
                    "name": "answer",
                    "default": "1",
                }
            ],
            style=prompt_style,
        )

        mocked_prompt.return_value = {}
        self.assertRaises(KeyboardInterrupt, self.cloudformationargs._set_rollback)

    @patch("fzfaws.cloudformation.helper.cloudformationargs.SNS")
    def test__set_notification(self, MockedSNS):
        sns = MockedSNS.return_value
        sns.arns = ["hello"]
        self.cloudformationargs._set_notification()
        sns.set_arns.assert_called_once_with(
            empty_allow=True, header="select sns topics to notify", multi_select=True
        )
        self.assertEqual(
            self.cloudformationargs._extra_args, {"NotificationARNs": ["hello"]}
        )

        sns.set_arns.reset_mock()
        self.cloudformationargs.cloudformation.stack_details = {
            "NotificationARNs": "111111"
        }
        self.cloudformationargs._set_notification(update=True)
        sns.set_arns.assert_called_once_with(
            empty_allow=True,
            header="select sns topics to notify\nOriginal value: 111111",
            multi_select=True,
        )

    @patch.object(Pyfzf, "get_local_file")
    def test__set_policy(self, mocked_file):
        mocked_file.return_value = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/policy.json"
        )
        self.cloudformationargs._set_policy()
        self.assertEqual(
            self.cloudformationargs._extra_args["StackPolicyBody"],
            json.dumps(
                {
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": "Update:*",
                            "Principal": "*",
                            "Resource": "*",
                        }
                    ]
                },
                indent=2,
            )
            + "\n",
        )
        mocked_file.assert_called_once_with(
            search_from_root=False,
            json=True,
            empty_allow=True,
            header="select the policy document you would like to use",
        )

        mocked_file.reset_mock()
        self.cloudformationargs._extra_args = {}
        self.cloudformationargs._set_policy(search_from_root=True, update=True)
        self.assertEqual(
            self.cloudformationargs._extra_args["StackPolicyDuringUpdateBody"],
            json.dumps(
                {
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": "Update:*",
                            "Principal": "*",
                            "Resource": "*",
                        }
                    ]
                },
                indent=2,
            )
            + "\n",
        )
        mocked_file.assert_called_once_with(
            search_from_root=True,
            json=True,
            empty_allow=True,
            header="select the policy document you would like to use",
        )

    @patch("fzfaws.cloudformation.helper.cloudformationargs.IAM")
    def test__set_permissions(self, MockedIAM):
        iam = MockedIAM.return_value
        iam.arns = ["hello"]
        self.cloudformationargs._set_permissions()
        iam.set_arns.assert_called_once_with(
            header="choose an IAM role to explicitly define CloudFormation's permissions\nNote: only IAM role can be assumed by CloudFormation is listed",
            service="cloudformation.amazonaws.com",
        )
        self.assertEqual(self.cloudformationargs.extra_args, {"RoleARN": "hello"})

        iam.set_arns.reset_mock()
        self.cloudformationargs.cloudformation.stack_details = {"RoleARN": "111111"}
        self.cloudformationargs._set_permissions(update=True)
        iam.set_arns.assert_called_once_with(
            header="select a role Choose an IAM role to explicitly define CloudFormation's permissions\nOriginal value: 111111",
            service="cloudformation.amazonaws.com",
        )

    @patch("fzfaws.cloudformation.helper.cloudformationargs.prompt")
    def test_set_tags(self, mocked_prompt):
        mocked_prompt.return_value = {}
        self.assertRaises(KeyboardInterrupt, self.cloudformationargs._set_tags)

        mocked_prompt.reset_mock()
        mocked_prompt.return_value = {"answer": "foo=boo&yes=no"}
        self.cloudformationargs._set_tags()
        self.assertEqual(
            self.cloudformationargs._extra_args,
            {"Tags": [{"Key": "foo", "Value": "boo"}, {"Key": "yes", "Value": "no"},]},
        )
        mocked_prompt.assert_called_once_with(
            [{"type": "input", "message": "Tags", "name": "answer", "validate": ANY,}],
            style=prompt_style,
        )

        mocked_prompt.reset_mock()
        self.cloudformationargs.cloudformation.stack_details = {
            "Tags": [{"Key": "foo", "Value": "boo"}, {"Key": "hello", "Value": "yes"}]
        }
        self.cloudformationargs._set_tags(update=True)
        mocked_prompt.assert_called_once_with(
            [
                {
                    "type": "input",
                    "message": "Tags",
                    "name": "answer",
                    "validate": ANY,
                    "default": "foo=boo&hello=yes",
                }
            ],
            style=prompt_style,
        )
