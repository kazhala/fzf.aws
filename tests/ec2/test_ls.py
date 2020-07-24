import json
import unittest
from unittest.mock import PropertyMock, patch
import sys
import io
import os
from fzfaws.utils import FileLoader, BaseSession
from fzfaws.ec2 import EC2
from fzfaws.ec2.ls_instance import ls_instance, dump_response
import boto3
from botocore.stub import Stubber
from pathlib import Path


class TestEC2ls(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput
        fileloader = FileLoader()
        config_path = Path(__file__).resolve().parent.joinpath("../data/fzfaws.yml")
        fileloader.load_config_file(config_path=str(config_path))

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_dump_response(self):
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        test_dict = {"hello": "world", "ResponseMetadata": {"hello": "wold"}}
        dump_response(test_dict)
        self.assertEqual(self.capturedOutput.getvalue(), '{\n    "hello": "world"\n}\n')

    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    @patch.object(EC2, "set_ec2_instance")
    def test_ls_instance(self, mocked_set_instance, mocked_client):
        response_data = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/ec2_instance.json"
        )
        with open(response_data, "r") as file:
            response = json.load(file)

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ec2 = boto3.client("ec2")
        stubber = Stubber(ec2)
        stubber.add_response("describe_instances", response[0])
        stubber.activate()
        mocked_client.return_value = ec2
        ls_instance(
            ipv4=True, privateip=True, dns=True, az=True, keyname=True, instanceid=True
        )
        self.assertEqual(
            self.capturedOutput.getvalue(), "None\nNone\nNone\nNone\nNone\nNone\n",
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ec2 = boto3.client("ec2")
        stubber = Stubber(ec2)
        stubber.add_response("describe_instances", response[0])
        stubber.activate()
        mocked_client.return_value = ec2
        ls_instance()
        self.assertRegex(self.capturedOutput.getvalue(), r"Reservations.*")

    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    @patch.object(EC2, "get_vpc_id")
    @patch.object(EC2, "set_ec2_instance")
    def test_ls_vpc(self, mocked_set_instance, mocked_vpc, mocked_client):
        response_data = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/ec2_vpc.json"
        )
        with open(response_data, "r") as file:
            response = json.load(file)
        mocked_vpc.return_value = ["vpc-0f07bd18d891bc5c0"]

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ec2 = boto3.client("ec2")
        stubber = Stubber(ec2)
        stubber.add_response("describe_vpcs", response[0])
        stubber.activate()
        mocked_client.return_value = ec2
        ls_instance(vpc=True)
        self.assertRegex(
            self.capturedOutput.getvalue(), r"State.*available",
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ls_instance(vpcid=True)
        self.assertEqual(
            self.capturedOutput.getvalue(), "vpc-0f07bd18d891bc5c0\n",
        )

    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    @patch.object(EC2, "get_volume_id")
    @patch.object(EC2, "set_ec2_instance")
    def test_ls_volume(self, mocked_set_instance, mocked_volume, mocked_client):
        response_data = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/ec2_volume.json"
        )
        with open(response_data, "r") as file:
            response = json.load(file)
        mocked_volume.return_value = ["vol-014718fdbcdf5ade8"]

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ec2 = boto3.client("ec2")
        stubber = Stubber(ec2)
        stubber.add_response("describe_volumes", response[0])
        stubber.activate()
        mocked_client.return_value = ec2
        ls_instance(volume=True)
        self.assertRegex(
            self.capturedOutput.getvalue(), r"VolumeType.*gp2",
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ls_instance(volumeid=True)
        self.assertEqual(
            self.capturedOutput.getvalue(), "vol-014718fdbcdf5ade8\n",
        )

    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    @patch.object(EC2, "get_subnet_id")
    @patch.object(EC2, "set_ec2_instance")
    def test_ls_subnet(self, mocked_set_instance, mocked_subnet, mocked_client):
        response_data = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/ec2_subnet.json"
        )
        with open(response_data, "r") as file:
            response = json.load(file)
        mocked_subnet.return_value = ["subnet-0084be888f20fa8eb"]

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ec2 = boto3.client("ec2")
        stubber = Stubber(ec2)
        stubber.add_response("describe_subnets", response[0])
        stubber.activate()
        mocked_client.return_value = ec2
        ls_instance(subnet=True)
        self.assertRegex(
            self.capturedOutput.getvalue(), r"State.*available",
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ls_instance(subnetid=True)
        self.assertEqual(
            self.capturedOutput.getvalue(), "subnet-0084be888f20fa8eb\n",
        )

    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    @patch.object(EC2, "get_security_groups")
    @patch.object(EC2, "set_ec2_instance")
    def test_ls_sg(self, mocked_set_instance, mocked_sg, mocked_client):
        response_data = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/ec2_sg.json"
        )
        with open(response_data, "r") as file:
            response = json.load(file)
        mocked_sg.return_value = ["sg-006ae18653dc5acd7"]

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ec2 = boto3.client("ec2")
        stubber = Stubber(ec2)
        stubber.add_response("describe_security_groups", response[0])
        stubber.activate()
        mocked_client.return_value = ec2
        ls_instance(sg=True)
        self.assertRegex(
            self.capturedOutput.getvalue(),
            r"GroupName.*hellotesting-EC2InstanceSecurityGroup",
        )
        mocked_sg.assert_called_with(
            multi_select=True, return_attr="id", no_progress=True
        )

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ls_instance(sgid=True)
        self.assertEqual(
            self.capturedOutput.getvalue(), "sg-006ae18653dc5acd7\n",
        )
        mocked_sg.assert_called_with(
            multi_select=True, return_attr="id", no_progress=True
        )

        mocked_sg.return_value = ["hellotesting-EC2InstanceSecurityGroup"]
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        ls_instance(sgname=True)
        self.assertEqual(
            self.capturedOutput.getvalue(), "hellotesting-EC2InstanceSecurityGroup\n",
        )
        mocked_sg.assert_called_with(
            multi_select=True, return_attr="name", no_progress=True
        )
