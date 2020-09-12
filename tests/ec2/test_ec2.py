import sys
import json
import io
import os
from types import GeneratorType
import unittest
from unittest.mock import ANY, patch
from fzfaws.ec2 import EC2
from botocore.paginate import Paginator
from fzfaws.utils import Pyfzf
from botocore.waiter import Waiter
from fzfaws.utils import FileLoader
from pathlib import Path


class TestEC2(unittest.TestCase):
    def setUp(self):
        fileloader = FileLoader()
        config_path = Path(__file__).resolve().parent.joinpath("../data/fzfaws.yml")
        fileloader.load_config_file(config_path=str(config_path))
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput
        self.ec2 = EC2()

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_constructor(self):
        self.assertEqual(self.ec2.profile, "default")
        self.assertEqual(self.ec2.region, "us-east-1")
        self.assertEqual(self.ec2.instance_ids, [""])
        self.assertEqual(self.ec2.instance_list, [{}])

        ec2 = EC2(profile="master", region="us-east-1")
        self.assertEqual(ec2.profile, "master")
        self.assertEqual(ec2.region, "us-east-1")
        self.assertEqual(self.ec2.instance_ids, [""])
        self.assertEqual(self.ec2.instance_list, [{}])

    @patch.object(EC2, "_instance_generator")
    @patch.object(Paginator, "paginate")
    @patch.object(Pyfzf, "process_list")
    @patch.object(Pyfzf, "execute_fzf")
    def test_set_ec2_instance(
        self, mocked_fzf_execute, mocked_fzf_list, mocked_result, mocked_generator
    ):
        # normal multi select test
        file_path = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(file_path, "../data/ec2_instance.json")
        with open(json_path, "r") as json_file:
            mocked_result.return_value = json.load(json_file)

        mocked_fzf_execute.return_value = [
            "InstanceId: 11111111 | InstanceType: t2.micro | Status: running | Name: meal-Bean-10PYXE0G1F4HS | KeyName: ap-southeast-2_playground | PublicDnsName: ec2-13-238-143-201.ap-southeast-2.compute.amazonaws.com | PublicIpAddress: 13.238.143.201 | PrivateIpAddress: 172.31.2.33",
            "InstanceId: 22222222 | InstanceType: t2.micro | Status: stopped | Name: default-ubuntu | KeyName: ap-southeast-2_playground | PublicDnsName: None | PublicIpAddress: None | PrivateIpAddress: 172.31.11.122",
        ]
        mocked_generator.return_value = [
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
                "PublicDnsName": None,
                "PublicIpAddress": None,
                "PrivateIpAddress": "172.31.11.122",
            },
        ]
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
                    "PublicDnsName": None,
                    "PublicIpAddress": None,
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
        mocked_fzf_execute.assert_called_with(
            multi_select=True, header=None, print_col=0
        )
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
                    "PublicDnsName": None,
                    "PublicIpAddress": None,
                    "PrivateIpAddress": "172.31.11.122",
                },
            ],
        )

        # normal single select test
        mocked_fzf_execute.return_value = "InstanceId: 11111111 | InstanceType: t2.micro | Status: running | Name: meal-Bean-10PYXE0G1F4HS | KeyName: ap-southeast-2_playground | PublicDnsName: ec2-13-238-143-201.ap-southeast-2.compute.amazonaws.com | PublicIpAddress: 13.238.143.201 | PrivateIpAddress: 172.31.2.33"
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
        mocked_fzf_execute.assert_called_with(
            multi_select=False, header="hello", print_col=0
        )

        # empty test
        self.ec2.instance_list[:] = [{}]
        self.ec2.instance_ids = [""]
        mocked_fzf_execute.return_value = ""
        mocked_result.return_value = [{"Reservations": []}]
        self.assertEqual(self.ec2.instance_ids, [""])
        self.assertEqual(self.ec2.instance_list, [{}])

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
            self.assertEqual(kwargs["WaiterConfig"], {"Delay": 10, "MaxAttempts": 60})

        mocked_wait.side_effect = test_waiter_arg2
        self.ec2.instance_ids = ["22222222"]
        self.ec2.wait("instance_status_ok", "hello")

        # test no config for watier
        del os.environ["FZFAWS_EC2_WAITER"]
        del os.environ["FZFAWS_GLOBAL_WAITER"]
        mocked_wait.side_effect = test_waiter_arg1
        self.ec2.instance_ids = ["11111111"]
        self.ec2.wait("instance_status_ok", "hello")
        self.assertRegex(
            self.capturedOutput.getvalue(),
            r"^| hello.*$",
        )

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
        self.ec2.get_security_groups()
        mocked_fzf_list.assert_called_with(
            ANY,
            "GroupId",
            "GroupName",
            "Name",
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
            ANY,
            "GroupName",
            "Name",
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
            ANY,
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
            ANY,
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
            ANY,
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

    @patch.object(Pyfzf, "process_list")
    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Paginator, "paginate")
    def test_get_vpc_id(self, mocked_result, mocked_fzf_execute, mocked_fzf_list):
        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/ec2_vpc.json"
        )
        with open(data_path, "r") as json_file:
            mocked_result.return_value = json.load(json_file)

        # normal test
        mocked_fzf_execute.return_value = "11111111"
        self.ec2.get_vpc_id()
        mocked_fzf_list.assert_called_with(
            ANY,
            "VpcId",
            "IsDefault",
            "CidrBlock",
            "Name",
        )
        mocked_fzf_execute.assert_called_with(
            empty_allow=True, multi_select=False, header=None
        )

        # custom settings
        mocked_fzf_execute.return_value = ["11111111", "22222222"]
        self.ec2.get_vpc_id(multi_select=True, header="hello")
        mocked_fzf_execute.assert_called_with(
            empty_allow=True, multi_select=True, header="hello"
        )

    def test_instance_generator(self):
        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/ec2_instance.json"
        )
        with open(data_path, "r") as json_file:
            response = json.load(json_file)

        generator = self.ec2._instance_generator(response[0]["Reservations"])
        self.assertIsInstance(generator, GeneratorType)
        for instance in generator:
            self.assertIsInstance(instance, dict)
            self.assertRegex(instance["InstanceId"], r"[0-9]*")

    def test_name_tag_generator(self):
        data = [
            {
                "CidrBlock": "10.1.0.0/16",
                "State": "available",
                "VpcId": "vpc-0f07bd18d891bc5c0",
                "OwnerId": "111111",
                "InstanceTenancy": "default",
                "IsDefault": False,
                "Tags": [
                    {"Key": "aws:cloudformation:logical-id", "Value": "CustomVPC"},
                    {"Key": "Name", "Value": "playground"},
                ],
            },
            {
                "CidrBlock": "172.31.0.0/16",
                "State": "available",
                "VpcId": "vpc-5c03313b",
                "OwnerId": "111111",
                "InstanceTenancy": "default",
                "IsDefault": True,
            },
        ]
        transformed = [
            {
                "CidrBlock": "10.1.0.0/16",
                "State": "available",
                "VpcId": "vpc-0f07bd18d891bc5c0",
                "OwnerId": "111111",
                "InstanceTenancy": "default",
                "IsDefault": False,
                "Tags": [
                    {"Key": "aws:cloudformation:logical-id", "Value": "CustomVPC"},
                    {"Key": "Name", "Value": "playground"},
                ],
                "Name": "playground",
            },
            {
                "CidrBlock": "172.31.0.0/16",
                "State": "available",
                "VpcId": "vpc-5c03313b",
                "OwnerId": "111111",
                "InstanceTenancy": "default",
                "IsDefault": True,
                "Name": None,
            },
        ]
        generator = self.ec2._name_tag_generator(data)
        self.assertEqual(transformed, list(generator))

    def test_instance_id_generator(self):
        json_path = (
            Path(__file__).resolve().parent.joinpath("../data/ec2_instance.json")
        )
        with json_path.open("r") as file:
            response = json.load(file)[0]["Reservations"]
        generator = self.ec2._instance_id_generator(response)
        self.assertEqual(
            [
                {"InstanceId": "11111111", "Name": "meal-Bean-10PYXE0G1F4HS"},
                {"InstanceId": "22222222", "Name": "default-ubuntu"},
            ],
            list(generator),
        )
