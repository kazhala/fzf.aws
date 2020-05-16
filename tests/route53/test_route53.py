import unittest
import io
import sys
from unittest.mock import patch
from fzfaws.route53 import Route53
from fzfaws.utils import BaseSession, Pyfzf


class TestRoute53(unittest.TestCase):
    def setUp(self):
        capturedOutput = io.StringIO()
        sys.stdout = capturedOutput
        self.route53 = Route53()

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_constructor(self):
        self.assertEqual(self.route53.zone_ids, [""])
        self.assertEqual(self.route53.profile, None)
        self.assertEqual(self.route53.region, None)

        route53 = Route53(profile="root", region="ap-southeast-2")
        self.assertEqual(route53.zone_ids, [""])
        self.assertEqual(route53.profile, "root")
        self.assertEqual(route53.region, "ap-southeast-2")

    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Pyfzf, "process_list")
    @patch.object(BaseSession, "get_paginated_result")
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

        self.route53.set_zone_id(multi_select=True)
        self.assertEqual(self.route53.zone_ids, ["111111"])

        self.route53.set_zone_id(zone_ids=["111111", "222222"])
        self.assertEqual(self.route53.zone_ids, ["111111", "222222"])

        self.route53.zone_ids = [""]
        self.route53.set_zone_id(zone_ids="222222")
        self.assertEqual(self.route53.zone_ids, ["222222"])

    def test_process_hosted_zone(self):
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

        test_list = []
        result = self.route53._process_hosted_zone(test_list)
        self.assertEqual([], result)

        test_list = [
            {"Id": "/hostedzone/111111",},
            {"Id": "/hostedzone/222222",},
        ]
        result = self.route53._process_hosted_zone(test_list)
        self.assertEqual(
            [{"Id": "111111", "Name": "N/A"}, {"Id": "222222", "Name": "N/A"},], result
        )
