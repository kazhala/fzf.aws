import sys
import io
import unittest
from unittest.mock import patch
from fzfaws.kms import KMS
from fzfaws.utils import Pyfzf
from botocore.paginate import Paginator


class TestKMS(unittest.TestCase):
    def setUp(self):
        capturedOutput = io.StringIO()
        sys.stdout = capturedOutput
        self.kms = KMS()

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_constructor(self):
        self.assertEqual(self.kms.profile, None)
        self.assertEqual(self.kms.region, None)
        self.assertEqual(self.kms.keyids, [""])

        kms = KMS(profile="root", region="us-east-1")
        self.assertEqual(kms.profile, "root")
        self.assertEqual(kms.region, "us-east-1")
        self.assertEqual(kms.keyids, [""])

    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Pyfzf, "process_list")
    @patch.object(Paginator, "paginate")
    def test_set_keyids(self, mocked_result, mocked_fzf_list, mocked_fzf_execute):
        mocked_result.return_value = [
            {
                "Aliases": [
                    {
                        "AliasName": "alias/S3Encrypt",
                        "AliasArn": "arn:aws:kms:ap-southeast-2:11111111:alias/S3Encrypt",
                        "TargetKeyId": "11111111-f48d-48b8-90d4-11111111",
                    },
                    {
                        "AliasName": "alias/aws/acm",
                        "AliasArn": "arn:aws:kms:ap-southeast-2:11111111:alias/aws/acm",
                        "TargetKeyId": "11111111-1261-4941-9731-11111111",
                    },
                ],
                "Truncated": False,
                "ResponseMetadata": {"HTTPStatusCode": 200, "RetryAttempts": 0,},
            }
        ]

        # general test
        mocked_fzf_execute.return_value = "11111111-1261-4941-9731-11111111"
        self.kms.set_keyids()
        mocked_fzf_list.assert_called_with(
            [
                {
                    "AliasName": "alias/S3Encrypt",
                    "AliasArn": "arn:aws:kms:ap-southeast-2:11111111:alias/S3Encrypt",
                    "TargetKeyId": "11111111-f48d-48b8-90d4-11111111",
                },
                {
                    "AliasName": "alias/aws/acm",
                    "AliasArn": "arn:aws:kms:ap-southeast-2:11111111:alias/aws/acm",
                    "TargetKeyId": "11111111-1261-4941-9731-11111111",
                },
            ],
            "TargetKeyId",
            "AliasName",
            "AliasArn",
        )
        self.assertEqual(self.kms.keyids, ["11111111-1261-4941-9731-11111111"])

        # parameter test
        self.kms.set_keyids(header="hello", multi_select=True, empty_allow=False)
        mocked_fzf_execute.assert_called_with(
            header="hello", multi_select=True, empty_allow=False
        )

        mocked_fzf_execute.reset_mock()
        self.kms.set_keyids(keyids="11111111-1261-4941-9731-11111111")
        mocked_fzf_execute.assert_not_called()
        self.assertEqual(self.kms.keyids, ["11111111-1261-4941-9731-11111111"])

        mocked_fzf_execute.reset_mock()
        self.kms.set_keyids(keyids=["11111111-1261-4941-9731-11111111"])
        mocked_fzf_execute.assert_not_called()
        self.assertEqual(self.kms.keyids, ["11111111-1261-4941-9731-11111111"])

        # empty result test
        mocked_result.return_value = []
        mocked_fzf_execute.reset_mock()
        mocked_fzf_execute.return_value = ""
        mocked_fzf_list.reset_mock()
        self.kms.keyids = [""]
        self.kms.set_keyids()
        mocked_fzf_list.assert_not_called()
        mocked_fzf_execute.assert_called_once()
        self.assertEqual(self.kms.keyids, [""])
