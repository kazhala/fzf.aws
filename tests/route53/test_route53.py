import unittest
import os
import io
import sys
from unittest.mock import patch
from fzfaws.route53 import Route53
from fzfaws.utils import Pyfzf, FileLoader
from botocore.paginate import Paginator


class TestRoute53(unittest.TestCase):
    def setUp(self):
        fileloader = FileLoader()
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../../fzfaws/fzfaws.yml"
        )
        fileloader.load_config_file(config_path=config_path)
        capturedOutput = io.StringIO()
        sys.stdout = capturedOutput
        self.route53 = Route53()

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_constructor(self):
        self.assertEqual(self.route53.zone_ids, [""])
        self.assertEqual(self.route53.profile, "default")
        self.assertEqual(self.route53.region, "ap-southeast-2")

        route53 = Route53(profile="root", region="us-west-1")
        self.assertEqual(route53.zone_ids, [""])
        self.assertEqual(route53.profile, "root")
        self.assertEqual(route53.region, "us-west-1")

    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Pyfzf, "process_list")
    @patch.object(Paginator, "paginate")
    def test_set_zone_id(self, mocked_result, mocked_fzf_process, mocked_fzf_execute):
        mocked_result.return_value = [
            {
                "ResponseMetadata": {"HTTPStatusCode": 200, "RetryAttempts": 0,},
                "HostedZones": [
                    {
                        "Id": "/hostedzone/111111",
                        "Name": "bilibonshop.xyz.",
                        "Config": {"PrivateZone": False},
                        "ResourceRecordSetCount": 7,
                    },
                    {
                        "Id": "/hostedzone/222222",
                        "Name": "mealternative.com.",
                        "Config": {
                            "Comment": "HostedZone created by Route53 Registrar",
                            "PrivateZone": False,
                        },
                        "ResourceRecordSetCount": 7,
                    },
                ],
                "IsTruncated": False,
                "MaxItems": "100",
            }
        ]

        # general test
        mocked_fzf_execute.return_value = "111111"
        self.route53.set_zone_id()
        mocked_fzf_process.assert_called_with(
            [
                {"Id": "111111", "Name": "bilibonshop.xyz."},
                {"Id": "222222", "Name": "mealternative.com."},
            ],
            "Id",
            "Name",
        )
        self.assertEqual(self.route53.zone_ids, ["111111"])

        # parameter test
        self.route53.set_zone_id(multi_select=True)
        self.assertEqual(self.route53.zone_ids, ["111111"])

        self.route53.set_zone_id(zone_ids=["111111", "222222"])
        self.assertEqual(self.route53.zone_ids, ["111111", "222222"])

        self.route53.zone_ids = [""]
        self.route53.set_zone_id(zone_ids="222222")
        self.assertEqual(self.route53.zone_ids, ["222222"])

        # empty result test
        self.route53.zone_ids = [""]
        mocked_fzf_execute.reset_mock()
        mocked_fzf_process.reset_mock()
        mocked_fzf_execute.return_value = ""
        mocked_result.return_value = []
        self.route53.set_zone_id()
        mocked_fzf_process.assert_not_called()
        mocked_fzf_execute.assert_called_once()
        self.assertEqual(self.route53.zone_ids, [""])

    def test_process_hosted_zone(self):
        # general
        test_list = [
            {
                "Id": "/hostedzone/111111",
                "Name": "bilibonshop.xyz.",
                "Config": {"PrivateZone": False},
                "ResourceRecordSetCount": 7,
            },
            {
                "Id": "/hostedzone/222222",
                "Name": "mealternative.com.",
                "Config": {
                    "Comment": "HostedZone created by Route53 Registrar",
                    "PrivateZone": False,
                },
                "ResourceRecordSetCount": 7,
            },
        ]
        result = self.route53._process_hosted_zone(test_list)
        self.assertEqual(
            [
                {"Id": "111111", "Name": "bilibonshop.xyz."},
                {"Id": "222222", "Name": "mealternative.com."},
            ],
            result,
        )

        # empty result test
        test_list = []
        result = self.route53._process_hosted_zone(test_list)
        self.assertEqual([], result)

        # missing attr test
        test_list = [
            {"Id": "/hostedzone/111111",},
            {"Id": "/hostedzone/222222",},
        ]
        result = self.route53._process_hosted_zone(test_list)
        self.assertEqual(
            [{"Id": "111111", "Name": None}, {"Id": "222222", "Name": None}], result,
        )
