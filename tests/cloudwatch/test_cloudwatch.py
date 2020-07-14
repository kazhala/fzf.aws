import io
import sys
import os
import unittest
from unittest.mock import patch
from fzfaws.cloudwatch import Cloudwatch
from fzfaws.utils import Pyfzf, FileLoader
from botocore.paginate import Paginator


class TestCloudWwatch(unittest.TestCase):
    def setUp(self):
        fileloader = FileLoader()
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../../fzfaws/fzfaws.yml"
        )
        fileloader.load_config_file(config_path=config_path)
        capturedOutput = io.StringIO()
        sys.stdout = capturedOutput
        self.cloudwatch = Cloudwatch()

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_constructor(self):
        self.assertEqual(self.cloudwatch.profile, "default")
        self.assertEqual(self.cloudwatch.region, "ap-southeast-2")
        self.assertEqual(self.cloudwatch.arns, [""])

        cloudwatch = Cloudwatch(profile="root", region="us-east-1")
        self.assertEqual(cloudwatch.profile, "root")
        self.assertEqual(cloudwatch.region, "us-east-1")
        self.assertEqual(cloudwatch.arns, [""])

    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Pyfzf, "process_list")
    @patch.object(Paginator, "paginate")
    def test_set_arns(self, mocked_result, mocked_fzf_list, mocked_fzf_execute):
        mocked_result.return_value = [
            {
                "CompositeAlarms": [],
                "MetricAlarms": [
                    {
                        "AlarmName": "Auto-check-drift-CloudWatchAlarms-11111111",
                        "AlarmArn": "arn:aws:cloudwatch:ap-southeast-2:11111111:alarm:Auto-check-drift-CloudWatchAlarms-11111111",
                        "AlarmDescription": "Drift status of cloudformation stacks",
                        "StateValue": "OK",
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
        mocked_fzf_execute.return_value = ""
        mocked_result.return_value = []
        self.cloudwatch.arns = [""]
        self.cloudwatch.set_arns()
        self.assertEqual(self.cloudwatch.arns, [""])
        mocked_fzf_list.assert_not_called()
        mocked_fzf_execute.assert_called_once()
