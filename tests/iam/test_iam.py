import io
import sys
import unittest
from unittest.mock import patch
from fzfaws.iam.iam import IAM
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.session import BaseSession


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
    @patch.object(Pyfzf, "append_fzf")
    @patch.object(Pyfzf, "execute_fzf")
    def test_no_result(self, mocked_fzf_execute, mocked_fzf_append, mocked_result):
        mocked_result.return_value = []
        mocked_fzf_execute.return_value = ""
        self.iam.set_arns(service="cloudformation.amazonaws.com")
        mocked_fzf_append.assert_not_called()
        mocked_fzf_execute.assert_called_once()
        self.assertEqual("", self.iam.arns[0])

    @patch.object(BaseSession, "get_paginated_result")
    @patch.object(Pyfzf, "process_list")
    @patch.object(Pyfzf, "append_fzf")
    @patch.object(Pyfzf, "execute_fzf")
    def test_setarns(
        self, mocked_fzf_execute, mocked_fzf_append, mocked_fzf_list, mocked_result
    ):
        # test service IAM
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
        mocked_fzf_execute.return_value = (
            "arn:aws:iam::378756445655:role/admincloudformaitontest"
        )
        self.iam.set_arns(service="cloudformation.amazonaws.com")
        mocked_fzf_append.assert_called_with(
            "RoleName: admincloudformaitontest  Arn: arn:aws:iam::378756445655:role/admincloudformaitontest"
        )
        self.assertEqual(
            "arn:aws:iam::378756445655:role/admincloudformaitontest", self.iam.arns[0]
        )

        # no restriction test
        self.iam.set_arns()
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
