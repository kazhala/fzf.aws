import sys
import io
import unittest
from unittest.mock import patch
from fzfaws.ec2 import EC2


class TestEC2(unittest.TestCase):
    def setUp(self):
        capturedOutput = io.StringIO()
        sys.stdout = capturedOutput
        self.ec2 = EC2()

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_constructor(self):
        self.assertEqual(self.ec2.profile, None)
        self.assertEqual(self.ec2.region, None)

        ec2 = EC2(profile="root", region="us-east-1")
        self.assertEqual(ec2.profile, "root")
        self.assertEqual(ec2.region, "us-east-1")
