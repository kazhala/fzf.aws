import unittest
import os
import io
import sys
from unittest.mock import patch
from fzfaws.sns import SNS
from fzfaws.utils import Pyfzf, FileLoader
from botocore.paginate import Paginator


class TestSNS(unittest.TestCase):
    def setUp(self):
        fileloader = FileLoader()
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../../fzfaws.yml"
        )
        fileloader.load_config_file(config_path=config_path)
        capturedOutput = io.StringIO()
        sys.stdout = capturedOutput
        self.sns = SNS()

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_constructor(self):
        self.assertEqual(self.sns.profile, "default")
        self.assertEqual(self.sns.region, "ap-southeast-2")
        self.assertEqual(self.sns.arns, [""])

        sns = SNS(profile="root", region="us-east-2")
        self.assertEqual(sns.profile, "root")
        self.assertEqual(sns.region, "us-east-2")
        self.assertEqual(sns.arns, [""])

    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Pyfzf, "process_list")
    @patch.object(Paginator, "paginate")
    def test_set_arns(self, mocked_result, mocked_fzf_list, mocked_fzf_execute):
        mocked_result.return_value = [
            {
                "Topics": [
                    {"TopicArn": "arn:aws:sns:ap-southeast-2:11111111:cformtesting"},
                    {"TopicArn": "arn:aws:sns:ap-southeast-2:11111111:s3testing"},
                ],
                "ResponseMetadata": {
                    "RequestId": "5a016407-2e05-5462-9513-333e45a424c3",
                    "HTTPStatu sCode": 200,
                    "RetryAttempts": 0,
                },
            }
        ]

        # general
        mocked_fzf_execute.return_value = (
            "arn:aws:sns:ap-southeast-2:11111111:s3testing"
        )
        self.sns.set_arns()
        self.assertEqual(
            self.sns.arns, ["arn:aws:sns:ap-southeast-2:11111111:s3testing"]
        )
        mocked_fzf_list.assert_called_with(
            [
                {"TopicArn": "arn:aws:sns:ap-southeast-2:11111111:cformtesting"},
                {"TopicArn": "arn:aws:sns:ap-southeast-2:11111111:s3testing"},
            ],
            "TopicArn",
        )

        # parameter test
        self.sns.set_arns(empty_allow=True, header="hello", multi_select=True)
        mocked_fzf_execute.assert_called_with(
            empty_allow=True, header="hello", multi_select=True
        )
        self.assertEqual(
            self.sns.arns, ["arn:aws:sns:ap-southeast-2:11111111:s3testing"]
        )

        self.sns.arns = [""]
        self.sns.set_arns(arns="11111111")
        self.assertEqual(self.sns.arns, ["11111111"])

        self.sns.set_arns(arns=["11111111", "222222"])
        self.assertEqual(self.sns.arns, ["11111111", "222222"])

        # empty result test
        mocked_fzf_execute.return_value = ""
        mocked_fzf_execute.reset_mock()
        mocked_result.return_value = []
        self.sns.arns = [""]
        mocked_fzf_list.reset_mock()
        self.sns.set_arns()
        mocked_fzf_list.assert_not_called()
        mocked_fzf_execute.assert_called_once()
        self.assertEqual(self.sns.arns, [""])
