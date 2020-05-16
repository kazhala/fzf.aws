import io
import sys
import unittest
from unittest.mock import patch
from fzfaws.iam import IAM
from fzfaws.utils import Pyfzf, BaseSession


class TestIAM(unittest.TestCase):
    def setUp(self):
        self.iam = IAM(profile="default", region="ap-southeast-2")
        capturedOutput = io.StringIO()
        sys.stdout = capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_constructor(self):
        self.assertEqual([""], self.iam.arns)
        self.assertEqual("default", self.iam.profile)
        self.assertEqual("ap-southeast-2", self.iam.region)

        iam = IAM()
        self.assertEqual(None, iam.profile)
        self.assertEqual(None, iam.region)

    @patch.object(BaseSession, "get_paginated_result")
    @patch.object(Pyfzf, "process_list")
    @patch.object(Pyfzf, "append_fzf")
    @patch.object(Pyfzf, "execute_fzf")
    def test_setarns(
        self, mocked_fzf_execute, mocked_fzf_append, mocked_fzf_list, mocked_result
    ):
        mocked_result.return_value = [
            {
                "Roles": [
                    {
                        "Path": "/",
                        "RoleName": "admincloudformaitontest",
                        "RoleId": "AROAVQL5EWXLRDZGWYAU2",
                        "Arn": "arn:aws:iam::378756445655:role/admincloudformaitontest",
                        "CreateDate": "2010-09-09",
                        "AssumeRolePolicyDocument": {
                            "Version": "2012-10-17",
                            "Statement": [
                                {
                                    "Sid": "",
                                    "Effect": "Allow",
                                    "Principal": {
                                        "Service": "cloudformation.amazonaws.com"
                                    },
                                    "Action": "sts:AssumeRole",
                                }
                            ],
                        },
                        "Description": "Allows CloudFormation to create and manage AWS stacks and resources on your behalf.",
                        "MaxSessionDuration": 3600,
                    }
                ]
            }
        ]

        # general test
        mocked_fzf_execute.return_value = (
            "arn:aws:iam::378756445655:role/admincloudformaitontest"
        )
        self.iam.set_arns()
        self.assertEqual(
            self.iam.arns, ["arn:aws:iam::378756445655:role/admincloudformaitontest"]
        )
        mocked_fzf_append.assert_not_called()
        mocked_fzf_list.assert_called_with(
            [
                {
                    "Path": "/",
                    "RoleName": "admincloudformaitontest",
                    "RoleId": "AROAVQL5EWXLRDZGWYAU2",
                    "Arn": "arn:aws:iam::378756445655:role/admincloudformaitontest",
                    "CreateDate": "2010-09-09",
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Sid": "",
                                "Effect": "Allow",
                                "Principal": {
                                    "Service": "cloudformation.amazonaws.com"
                                },
                                "Action": "sts:AssumeRole",
                            }
                        ],
                    },
                    "Description": "Allows CloudFormation to create and manage AWS stacks and resources on your behalf.",
                    "MaxSessionDuration": 3600,
                }
            ],
            "RoleName",
            "Arn",
        )

        # parameter test
        self.iam.set_arns(service="cloudformation.amazonaws.com")
        mocked_fzf_append.assert_called_with(
            "RoleName: admincloudformaitontest  Arn: arn:aws:iam::378756445655:role/admincloudformaitontest"
        )

        mocked_fzf_append.reset_mock()
        self.iam.set_arns(service="hello")
        mocked_fzf_append.assert_not_called()

        mocked_fzf_list.reset_mock()
        self.iam.set_arns(header="hello", empty_allow=True, multi_select=True)
        mocked_fzf_list.assert_called_once()
        mocked_fzf_execute.assert_called_with(
            empty_allow=True, header="hello", multi_select=True, print_col=4
        )

        self.iam.set_arns(arns="111111")
        self.assertEqual(self.iam.arns, ["111111"])

        self.iam.set_arns(arns=["111111", "222222"])
        self.assertEqual(self.iam.arns, ["111111", "222222"])

        # empty result test
        self.iam.arns = [""]
        mocked_fzf_execute.reset_mock()
        mocked_fzf_append.reset_mock()
        mocked_result.return_value = []
        mocked_fzf_execute.return_value = ""
        self.iam.set_arns(service="cloudformation.amazonaws.com")
        mocked_fzf_append.assert_not_called()
        mocked_fzf_execute.assert_called_once()
        self.assertEqual([""], self.iam.arns)
