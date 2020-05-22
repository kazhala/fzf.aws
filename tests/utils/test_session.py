import unittest
from unittest.mock import patch, PropertyMock
from fzfaws.utils import BaseSession, Pyfzf
from boto3.session import Session
import boto3
from botocore.stub import Stubber


class TestSession(unittest.TestCase):
    def test_empty_init(self):
        session = BaseSession(service_name="ec2")
        self.assertEqual(None, session.profile)
        self.assertEqual(None, session.region)

    def test_param_profile_region(self):
        session = BaseSession(
            profile="root", region="ap-southeast-2", service_name="ec2"
        )
        self.assertEqual("root", session.profile)
        self.assertEqual("ap-southeast-2", session.region)

    @patch.object(Pyfzf, "append_fzf")
    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Session, "available_profiles", new_callable=PropertyMock)
    def test_fzf_profile(self, mocked_profile, mocked_fzf_execute, mocked_fzf_append):
        mocked_profile.return_value = ["root", "default", "hello"]

        mocked_fzf_execute.return_value = "root"
        session = BaseSession(profile=True, region=None, service_name="ec2")
        self.assertEqual("root", session.profile)
        mocked_fzf_append.assert_called_with("hello\n")

    @patch.object(Pyfzf, "append_fzf")
    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Session, "get_available_regions")
    def test_fzf_region(self, mocked_region, mocked_fzf_execute, mocked_fzf_append):
        mocked_region.return_value = ["ap-southeast-2", "ap-southeast-1"]

        mocked_fzf_execute.return_value = "ap-southeast-2"
        session = BaseSession(profile=None, region=True, service_name="ec2")
        self.assertEqual("ap-southeast-2", session.region)
        mocked_fzf_append.assert_called_with("ap-southeast-1\n")

    # TODO: reference only for now
    def test_random(self):
        ec2 = boto3.client("ec2")
        stubber = Stubber(ec2)
        response = {"Reservations": []}
        stubber.add_response("describe_instances", response)
        stubber.activate()
        service_response = ec2.describe_instances()
        self.assertEqual(service_response, {"Reservations": []})
