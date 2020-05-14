import unittest
from unittest.mock import patch
from fzfaws.utils import (
    check_dict_value_in_list,
    get_confirmation,
    remove_dict_from_list,
    search_dict_in_list,
    get_name_tag,
)


class TestUtil(unittest.TestCase):
    def test_remove_dict_from_list(self):
        test_list = [{"hello": "world"}, {"hello": "no"}]
        test_list = remove_dict_from_list("no", test_list, "hello")
        self.assertEqual(test_list, [{"hello": "world"}])
        test_list = remove_dict_from_list("afasdfa", test_list, "bbbb")
        self.assertEqual(test_list, [{"hello": "world"}])

    def test_search_dict_in_list(self):
        test_list = [{"hello": "world"}, {"hello": "no"}]
        result = search_dict_in_list("no", test_list, "hello")
        self.assertEqual(result, {"hello": "no"})
        result = search_dict_in_list("asdf", test_list, "asdfa")
        self.assertEqual(result, {})
        test_list = []
        result = search_dict_in_list("no", test_list, "hello")
        self.assertEqual(result, {})

    def test_check_dict_value_in_list(self):
        test_list = [{"hello": "world"}, {"hello": "no"}]
        result = check_dict_value_in_list("world", test_list, "hello")
        self.assertTrue(result)
        result = check_dict_value_in_list("yes", test_list, "yes")
        self.assertFalse(result)
        test_list = []
        result = check_dict_value_in_list("yes", test_list, "yes")
        self.assertFalse(result)

    @patch("builtins.input")
    def test_get_confirmation(self, mocked_input):
        mocked_input.return_value = "y"
        response = get_confirmation("Confirm?")
        self.assertTrue(response)
        mocked_input.return_value = "n"
        response = get_confirmation("Confirm?")
        self.assertFalse(response)

    def test_get_name_tag(self):
        test_data = {
            "Instances": [
                {
                    "AmiLaunchIndex": 0,
                    "InstanceType": "t2.micro",
                    "KeyName": "ap-southeast-2_playground",
                    "Monitoring": {"State": "disabled"},
                    "Placement": {
                        "AvailabilityZone": "ap-southeast-2b",
                        "GroupName": "",
                        "Tenancy": "default",
                    },
                    "PublicIpAddress": "13.238.143.201",
                    "State": {"Code": 16, "Name": "running"},
                    "StateTransitionReason": "",
                    "Architecture": "x86_64",
                    "BlockDeviceMappings": [
                        {
                            "DeviceName": "/dev/xvda",
                            "Ebs": {
                                "DeleteOnTermination": True,
                                "Status": "attached",
                                "VolumeId": "vol-03d755609d4783573",
                            },
                        }
                    ],
                    "EbsOptimized": False,
                    "EnaSupport": True,
                    "Hypervisor": "xen",
                    "NetworkInterfaces": [],
                    "RootDeviceName": "/dev/xvda",
                    "RootDeviceType": "ebs",
                    "SecurityGroups": [],
                    "SourceDestCheck": True,
                    "Tags": [
                        {"Key": "aws:ec2launchtemplate:version", "Value": "5"},
                        {
                            "Key": "aws:cloudformation:stack-name",
                            "Value": "awseb-e-wphtqnu48q-stack",
                        },
                        {
                            "Key": "elasticbeanstalk:environment-id",
                            "Value": "e-wphtqnu48q",
                        },
                        {
                            "Key": "aws:cloudformation:logical-id",
                            "Value": "AWSEBAutoScalingGroup",
                        },
                        {"Key": "Application", "Value": "mealternative"},
                        {"Key": "WebServer", "Value": "yes"},
                        {
                            "Key": "aws:cloudformation:stack-id",
                            "Value": "arn:aws:cloudformation:ap-southeast-2:378756445655:stack/awseb-e-wphtqnu48q-stack/26833f80-62c0-11ea-bba2-0a630e7b8d5e",
                        },
                        {
                            "Key": "aws:autoscaling:groupName",
                            "Value": "awseb-e-wphtqnu48q-stack-AWSEBAutoScalingGroup-1NRHWVE3L8P3",
                        },
                        {
                            "Key": "elasticbeanstalk:environment-name",
                            "Value": "meal-Bean-10PYXE0G1F4HS",
                        },
                        {"Key": "Name", "Value": "meal-Bean-10PYXE0G1F4HS"},
                    ],
                    "VirtualizationType": "hvm",
                    "CpuOptions": {"CoreCount": 1, "ThreadsPerCore": 1},
                    "CapacityReservationSpecification": {
                        "CapacityReservationPreference": "open"
                    },
                    "HibernationOptions": {"Configured": False},
                }
            ],
        }
        name = get_name_tag(test_data["Instances"][0])
        self.assertEqual(name, "meal-Bean-10PYXE0G1F4HS")
        test_data = {}
        name = get_name_tag(test_data)
        self.assertEqual(name, "N/A")
