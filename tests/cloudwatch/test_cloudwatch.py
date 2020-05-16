import io
import sys
import unittest
from unittest.mock import patch
from fzfaws.cloudwatch import Cloudwatch
from fzfaws.utils import BaseSession, Pyfzf


class TestCloudWwatch(unittest.TestCase):
    def setUp(self):
        capturedOutput = io.StringIO()
        sys.stdout = capturedOutput
        self.cloudwatch = Cloudwatch()

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_constructor(self):
        self.assertEqual(self.cloudwatch.profile, None)
        self.assertEqual(self.cloudwatch.region, None)
        self.assertEqual(self.cloudwatch.arns, [""])

        cloudwatch = Cloudwatch(profile="root", region="us-east-1")
        self.assertEqual(cloudwatch.profile, "root")
        self.assertEqual(cloudwatch.region, "us-east-1")
        self.assertEqual(cloudwatch.arns, [""])

    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Pyfzf, "process_list")
    @patch.object(BaseSession, "get_paginated_result")
    def set_arns(self, mocked_result, mocked_fzf_list, mocked_fzf_execute):
        mocked_result.return_value = [
            {
                "CompositeAlarms": [],
                "MetricAlarms": [
                    {
                        "AlarmName": "Auto-check-drift-CloudWatchAlarms-11111111",
                        "AlarmArn": "arn:aws:cloudwatch:ap-southeast-2:11111111:alarm:Auto-check-drift-CloudWatchAlarms-11111111",
                        "AlarmDescription": "Drift status of cloudformation stacks",
                        "StateValue": "OK",
                        "StateReason": "Threshold Crossed: 1 out of the last 1 datapoints [0.0 (23/04/20 13:17:00)] was not greater than or equal to the threshold (1.0) (minimum 1 datapoint for ALARM -> OK transition).",
                        "StateReasonData": '{"version":"1.0","queryDate":"2020-04-23T13:18:50.528+0000","startDate":"2020-04-23T13:17:00.000+0000","statistic":"Sum","period":60,"recentDatapoints":[0.0],"threshold":1.0}',
                        "MetricName": "drift",
                        "Namespace": "Cloudformation",
                        "Statistic": "Sum",
                        "Period": 60,
                        "EvaluationPeriods": 1,
                        "DatapointsToAlarm": 1,
                        "Threshold": 1.0,
                    },
                    {
                        "AlarmName": "awseb-e-wphtqnu48q-stack-AWSEBCloudwatchAlarmHigh-11111111",
                        "AlarmArn": "arn:aws:cloudwatch:ap-southeast-2:11111111:alarm:awseb-e-wphtqnu48q-stack-AWSEBCloudwatchAlarmHigh-11111111",
                        "AlarmDescription": "ElasticBeanstalk Default Scale Up alarm",
                        "StateValue": "OK",
                        "StateReason": "Threshold Crossed: 1 datapoint [41021.666666666664 (07/04/20 23:31:00)] was not greater than the threshold (6000000.0).",
                        "StateReasonData": '{"version":"1.0","queryDate":"2020-04-07T23:41:46.393+0000","startDate":"2020-04-07T23:31:00.000+0000","statistic":"Average","period":300,"recentDatapoints":[41021.666666666664],"threshold":6000000.0}',
                        "MetricName": "NetworkOut",
                        "Namespace": "AWS/EC2",
                        "Statistic": "Average",
                        "Dimensions": [
                            {
                                "Name": "AutoScalingGroupName",
                                "Value": "awseb-e-wphtqnu48q-stack-AWSEBAutoScalingGroup-1NRHWVE3L8P3",
                            }
                        ],
                        "Period": 300,
                        "EvaluationPeriods": 1,
                        "Threshold": 6000000.0,
                    },
                ],
                "ResponseMetadata": {
                    "RequestId": "344ce173-da3c-4de5-9d0d-04f5a13600d5",
                    "HTTPStatusCode": 200,
                    "RetryAttempts": 0,
                },
            }
        ]

        # general test
        mocked_fzf_execute.return_value = "arn:aws:cloudwatch:ap-southeast-2:11111111:alarm:Auto-check-drift-CloudWatchAlarms-11111111"
        self.cloudwatch.set_arns()
        self.assertEqual(
            self.cloudwatch.arns,
            [
                "arn:aws:cloudwatch:ap-southeast-2:11111111:alarm:Auto-check-drift-CloudWatchAlarms-11111111"
            ],
        )
        mocked_fzf_list.assert_called_with(
            [
                {
                    "AlarmName": "Auto-check-drift-CloudWatchAlarms-11111111",
                    "AlarmArn": "arn:aws:cloudwatch:ap-southeast-2:11111111:alarm:Auto-check-drift-CloudWatchAlarms-11111111",
                    "AlarmDescription": "Drift status of cloudformation stacks",
                    "StateValue": "OK",
                    "StateReason": "Threshold Crossed: 1 out of the last 1 datapoints [0.0 (23/04/20 13:17:00)] was not greater than or equal to the threshold (1.0) (minimum 1 datapoint for ALARM -> OK transition).",
                    "StateReasonData": '{"version":"1.0","queryDate":"2020-04-23T13:18:50.528+0000","startDate":"2020-04-23T13:17:00.000+0000","statistic":"Sum","period":60,"recentDatapoints":[0.0],"threshold":1.0}',
                    "MetricName": "drift",
                    "Namespace": "Cloudformation",
                    "Statistic": "Sum",
                    "Period": 60,
                    "EvaluationPeriods": 1,
                    "DatapointsToAlarm": 1,
                    "Threshold": 1.0,
                },
                {
                    "AlarmName": "awseb-e-wphtqnu48q-stack-AWSEBCloudwatchAlarmHigh-11111111",
                    "AlarmArn": "arn:aws:cloudwatch:ap-southeast-2:11111111:alarm:awseb-e-wphtqnu48q-stack-AWSEBCloudwatchAlarmHigh-11111111",
                    "AlarmDescription": "ElasticBeanstalk Default Scale Up alarm",
                    "StateValue": "OK",
                    "StateReason": "Threshold Crossed: 1 datapoint [41021.666666666664 (07/04/20 23:31:00)] was not greater than the threshold (6000000.0).",
                    "StateReasonData": '{"version":"1.0","queryDate":"2020-04-07T23:41:46.393+0000","startDate":"2020-04-07T23:31:00.000+0000","statistic":"Average","period":300,"recentDatapoints":[41021.666666666664],"threshold":6000000.0}',
                    "MetricName": "NetworkOut",
                    "Namespace": "AWS/EC2",
                    "Statistic": "Average",
                    "Dimensions": [
                        {
                            "Name": "AutoScalingGroupName",
                            "Value": "awseb-e-wphtqnu48q-stack-AWSEBAutoScalingGroup-1NRHWVE3L8P3",
                        }
                    ],
                    "Period": 300,
                    "EvaluationPeriods": 1,
                    "Threshold": 6000000.0,
                },
            ],
            "AlarmArn",
        )

        # parameter test
        mocked_fzf_list.reset_mock()
        self.cloudwatch.set_arns(empty_allow=True, header="hello", multi_select=True)
        mocked_fzf_execute.assert_called_with(
            empty_allow=True, multi_select=True, header="hello"
        )
        self.assertEqual(
            self.cloudwatch.arns,
            [
                "arn:aws:cloudwatch:ap-southeast-2:11111111:alarm:Auto-check-drift-CloudWatchAlarms-11111111"
            ],
        )

        mocked_fzf_execute.reset_mock()
        self.cloudwatch.set_arns(arns="11111111")
        self.assertEqual(self.cloudwatch.arns, ["11111111"])
        mocked_fzf_execute.assert_not_called()

        self.cloudwatch.set_arns(arns=["11111111", "22222222"])
        self.assertEqual(self.cloudwatch.arns, ["11111111", "22222222"])

        # empty result test
        mocked_fzf_execute.reset_mock()
        mocked_fzf_list.reset_mock()
        mocked_result = []
        self.cloudwatch.arns = []
        self.cloudwatch.set_arns()
        self.assertEqual(self.cloudwatch.arns, [""])
        mocked_fzf_list.assert_not_called()
        mocked_fzf_execute.assert_called_once()
