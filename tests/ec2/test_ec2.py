import sys
import json
import io
import os
import unittest
from unittest.mock import patch
from fzfaws.ec2 import EC2
from botocore.paginate import Paginator
from fzfaws.utils import Pyfzf
from botocore.waiter import Waiter
from fzfaws.utils import FileLoader


class TestEC2(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput
        self.ec2 = EC2()

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_constructor(self):
        self.assertEqual(self.ec2.profile, None)
        self.assertEqual(self.ec2.region, None)
        self.assertEqual(self.ec2.instance_ids, [""])
        self.assertEqual(self.ec2.instance_list, [])

        ec2 = EC2(profile="root", region="us-east-1")
        self.assertEqual(ec2.profile, "root")
        self.assertEqual(ec2.region, "us-east-1")
        self.assertEqual(self.ec2.instance_ids, [""])
        self.assertEqual(self.ec2.instance_list, [])

    @patch.object(Paginator, "paginate")
    @patch.object(Pyfzf, "process_list")
    @patch.object(Pyfzf, "execute_fzf")
    def test_set_ec2_instance(self, mocked_fzf_execute, mocked_fzf_list, mocked_result):
        # normal multi select test
        file_path = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(file_path, "../data/ec2_instance.json")
        with open(json_path, "r") as json_file:
            mocked_result.return_value = json.load(json_file)

        mocked_fzf_execute.return_value = ["11111111", "22222222"]
        self.ec2.set_ec2_instance()
        mocked_fzf_list.assert_called_with(
            [
                {
                    "InstanceId": "11111111",
                    "InstanceType": "t2.micro",
                    "Status": "running",
                    "Name": "meal-Bean-10PYXE0G1F4HS",
                    "KeyName": "ap-southeast-2_playground",
                    "PublicDnsName": "ec2-13-238-143-201.ap-southeast-2.compute.amazonaws.com",
                    "PublicIpAddress": "13.238.143.201",
                    "PrivateIpAddress": "172.31.2.33",
                },
                {
                    "InstanceId": "22222222",
                    "InstanceType": "t2.micro",
                    "Status": "stopped",
                    "Name": "default-ubuntu",
                    "KeyName": "ap-southeast-2_playground",
                    "PublicDnsName": "",
                    "PublicIpAddress": "N/A",
                    "PrivateIpAddress": "172.31.11.122",
                },
            ],
            "InstanceId",
            "Status",
            "InstanceType",
            "Name",
            "KeyName",
            "PublicDnsName",
            "PublicIpAddress",
            "PrivateIpAddress",
        )
        mocked_fzf_execute.assert_called_with(multi_select=True, header=None)
        self.assertEqual(self.ec2.instance_ids, ["11111111", "22222222"])
        self.assertEqual(
            self.ec2.instance_list,
            [
                {
                    "InstanceId": "11111111",
                    "InstanceType": "t2.micro",
                    "Status": "running",
                    "Name": "meal-Bean-10PYXE0G1F4HS",
                    "KeyName": "ap-southeast-2_playground",
                    "PublicDnsName": "ec2-13-238-143-201.ap-southeast-2.compute.amazonaws.com",
                    "PublicIpAddress": "13.238.143.201",
                    "PrivateIpAddress": "172.31.2.33",
                },
                {
                    "InstanceId": "22222222",
                    "InstanceType": "t2.micro",
                    "Status": "stopped",
                    "Name": "default-ubuntu",
                    "KeyName": "ap-southeast-2_playground",
                    "PublicDnsName": "",
                    "PublicIpAddress": "N/A",
                    "PrivateIpAddress": "172.31.11.122",
                },
            ],
        )

        # normal single select test
        self.ec2.instance_list.clear()
        self.ec2.instance_ids = [""]
        mocked_fzf_execute.return_value = "11111111"
        self.ec2.set_ec2_instance(multi_select=False, header="hello")
        self.assertEqual(self.ec2.instance_ids, ["11111111"])
        self.assertEqual(
            self.ec2.instance_list,
            [
                {
                    "InstanceId": "11111111",
                    "InstanceType": "t2.micro",
                    "Status": "running",
                    "Name": "meal-Bean-10PYXE0G1F4HS",
                    "KeyName": "ap-southeast-2_playground",
                    "PublicDnsName": "ec2-13-238-143-201.ap-southeast-2.compute.amazonaws.com",
                    "PublicIpAddress": "13.238.143.201",
                    "PrivateIpAddress": "172.31.2.33",
                }
            ],
        )
        mocked_fzf_execute.assert_called_with(multi_select=False, header="hello")

        # empty test
        self.ec2.instance_list.clear()
        self.ec2.instance_ids = [""]
        mocked_fzf_execute.return_value = ""
        mocked_result.return_value = [{"Reservations": []}]
        self.assertEqual(self.ec2.instance_ids, [""])
        self.assertEqual(self.ec2.instance_list, [])

    def test_print_instance_details(self):
        self.ec2.instance_ids = ["11111111"]
        self.ec2.instance_list = [
            {
                "InstanceId": "11111111",
                "InstanceType": "t2.micro",
                "Status": "running",
                "Name": "meal-Bean-10PYXE0G1F4HS",
                "KeyName": "ap-southeast-2_playground",
                "PublicDnsName": "ec2-13-238-143-201.ap-southeast-2.compute.amazonaws.com",
                "PublicIpAddress": "13.238.143.201",
                "PrivateIpAddress": "172.31.2.33",
            }
        ]
        self.ec2.print_instance_details()
        self.assertEqual(
            self.capturedOutput.getvalue(),
            "InstanceId: 11111111  Name: meal-Bean-10PYXE0G1F4HS\n",
        )

    @patch.object(Waiter, "wait")
    def test_wait(self, mocked_wait):
        def test_waiter_arg1(obj, **kwargs):
            self.assertEqual(kwargs["InstanceIds"], ["11111111"])
            self.assertEqual(kwargs["WaiterConfig"], {"Delay": 15, "MaxAttempts": 40})

        def test_waiter_arg2(obj, **kwargs):
            self.assertEqual(kwargs["InstanceIds"], ["22222222"])
            self.assertEqual(kwargs["WaiterConfig"], {"Delay": 10, "MaxAttempts": 50})

        mocked_wait.side_effect = test_waiter_arg1
        self.ec2.instance_ids = ["11111111"]
        self.ec2.wait("instance_status_ok", "hello")
        self.assertRegex(
            self.capturedOutput.getvalue(), r"^| hello.*$",
        )

        mocked_wait.side_effect = test_waiter_arg2
        fileloader = FileLoader()
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../../fzfaws.yml"
        )
        fileloader.load_config_file(config_path=config_path)
        self.ec2.instance_ids = ["22222222"]
        self.ec2.wait("instance_status_ok", "hello")

    @patch.object(Pyfzf, "process_list")
    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Paginator, "paginate")
    def test_get_security_groups(
        self, mocked_result, mocked_fzf_execute, mocked_fzf_list
    ):
        # normal nomulti select test
        file_path = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(file_path, "../data/ec2_sg.json")
        with open(json_path, "r") as json_file:
            mocked_result.return_value = json.load(json_file)

        mocked_fzf_execute.return_value = "sg-006ae18653dc5acd7"
        assert_array = [
            {
                "GroupName": "hellotesting-EC2InstanceSecurityGroup",
                "GroupId": "sg-006ae18653dc5acd7",
                "Tags": [
                    {"Key": "hasdf", "Value": "asdfa"},
                    {
                        "Key": "aws:cloudformation:stack-id",
                        "Value": "arn:aws:cloudformation:ap-southeast-2:111111:stack/hellotesting/05feb330-88f3-11ea-ae79-0aa5d4eec80a",
                    },
                    {
                        "Key": "aws:cloudformation:logical-id",
                        "Value": "EC2InstanceSecurityGroup",
                    },
                    {"Key": "aws:cloudformation:stack-name", "Value": "hellotesting",},
                ],
                "VpcId": "vpc-5c03313b",
                "Name": "N/A",
            },
            {
                "GroupName": "default-ssh",
                "GroupId": "sg-0106a116cd9343134",
                "Tags": [
                    {
                        "Key": "aws:cloudformation:stack-id",
                        "Value": "arn:aws:cloudformation:ap-southeast-2:111111:stack/SG-default/fd03c970-6d70-11ea-ba51-0a97b58f1090",
                    },
                    {"Key": "aws:cloudformation:stack-name", "Value": "SG-default"},
                    {"Key": "aws:cloudformation:logical-id", "Value": "DefaultSSHSG",},
                    {"Key": "Name", "Value": "default-ssh"},
                ],
                "VpcId": "vpc-5c03313b",
                "Name": "default-ssh",
            },
        ]
        self.ec2.get_security_groups()
        mocked_fzf_list.assert_called_with(
            assert_array, "GroupId", "GroupName", "Name",
        )
        mocked_fzf_execute.assert_called_with(
            multi_select=False, empty_allow=True, header=None
        )

        # custom settings
        mocked_fzf_execute.return_value = ["sg-006ae18653dc5acd7"]
        self.ec2.get_security_groups(
            multi_select=True, return_attr="name", header="hello"
        )
        mocked_fzf_list.assert_called_with(
            assert_array, "GroupName", "Name",
        )
        mocked_fzf_execute.assert_called_with(
            multi_select=True, empty_allow=True, header="hello"
        )

    @patch.object(Pyfzf, "process_list")
    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Paginator, "paginate")
    def test_get_instance_id(self, mocked_result, mocked_fzf_execute, mocked_fzf_list):
        # normal test
        file_path = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(file_path, "../data/ec2_instance.json")
        with open(json_path, "r") as json_file:
            mocked_result.return_value = json.load(json_file)

        mocked_fzf_execute.return_value = "11111111"
        self.ec2.get_instance_id()
        mocked_fzf_list.assert_called_with(
            [
                {"InstanceId": "11111111", "Name": "meal-Bean-10PYXE0G1F4HS"},
                {"InstanceId": "22222222", "Name": "default-ubuntu"},
            ],
            "InstanceId",
            "Name",
        )
        mocked_fzf_execute.assert_called_with(
            multi_select=False, empty_allow=True, header=None
        )

        # custom settings
        mocked_fzf_execute.return_value = ["11111111", "22222222"]
        self.ec2.get_instance_id(multi_select=True, header="hello")
        mocked_fzf_execute.assert_called_with(
            multi_select=True, empty_allow=True, header="hello"
        )

    @patch.object(Pyfzf, "process_list")
    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Paginator, "paginate")
    def test_get_subnet_id(self, mocked_result, mocked_fzf_execute, mocked_fzf_list):
        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/ec2_subnet.json"
        )
        with open(data_path, "r") as json_file:
            mocked_result.return_value = json.load(json_file)

        # normal test
        mocked_fzf_execute.return_value = "11111111"
        self.ec2.get_subnet_id()
        mocked_fzf_list.assert_called_with(
            [
                {
                    "AvailabilityZone": "ap-southeast-2a",
                    "CidrBlock": "172.31.32.0/20",
                    "SubnetId": "subnet-d31f089a",
                    "VpcId": "vpc-5c03313b",
                    "SubnetArn": "arn:aws:ec2:ap-southeast-2:111111:subnet/subnet-d31f089a",
                    "Name": "N/A",
                },
                {
                    "AvailabilityZone": "ap-southeast-2c",
                    "CidrBlock": "10.1.3.0/24",
                    "SubnetId": "subnet-07ff9f753e9552040",
                    "VpcId": "vpc-0f07bd18d891bc5c0",
                    "Tags": [
                        {
                            "Key": "aws:cloudformation:stack-id",
                            "Value": "arn:aws:cloudformation:ap-southeast-2:111111:stack/VPC-playground/9c001d70-763c-11ea-931a-025411181be4",
                        },
                        {"Key": "Name", "Value": "playground-PublicC"},
                        {
                            "Key": "aws:cloudformation:logical-id",
                            "Value": "PublicSubnetC",
                        },
                        {
                            "Key": "aws:cloudformation:stack-name",
                            "Value": "VPC-playground",
                        },
                    ],
                    "SubnetArn": "arn:aws:ec2:ap-southeast-2:111111:subnet/subnet-07ff9f753e9552040",
                    "Name": "playground-PublicC",
                },
            ],
            "SubnetId",
            "AvailabilityZone",
            "CidrBlock",
            "Name",
        )
        mocked_fzf_execute.assert_called_with(
            multi_select=False, empty_allow=True, header=None
        )

        # custom settings
        mocked_fzf_execute.return_value = ["11111111", "22222222"]
        self.ec2.get_subnet_id(multi_select=True, header="hello")
        mocked_fzf_execute.assert_called_with(
            multi_select=True, empty_allow=True, header="hello"
        )

    @patch.object(Pyfzf, "process_list")
    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Paginator, "paginate")
    def test_get_volume_id(self, mocked_result, mocked_fzf_execute, mocked_fzf_list):
        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/ec2_volume.json"
        )
        with open(data_path, "r") as json_file:
            mocked_result.return_value = json.load(json_file)

        # normal test
        mocked_fzf_execute.return_value = "11111111"
        self.ec2.get_volume_id()
        mocked_fzf_list.assert_called_with(
            [
                {
                    "VolumeId": "vol-03d755609d4783573",
                    "Iops": 100,
                    "VolumeType": "gp2",
                    "Name": "N/A",
                },
                {
                    "VolumeId": "vol-04bf0dd95936347fc",
                    "Iops": 100,
                    "VolumeType": "gp2",
                    "Name": "N/A",
                },
            ],
            "VolumeId",
            "Name",
        )
        mocked_fzf_execute.assert_called_with(
            multi_select=False, empty_allow=True, header=None
        )

        # custom settings
        mocked_fzf_execute.return_value = ["11111111", "22222222"]
        self.ec2.get_volume_id(multi_select=True, header="hello")
        mocked_fzf_execute.assert_called_with(
            multi_select=True, empty_allow=True, header="hello"
        )
