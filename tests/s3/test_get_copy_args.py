import os
import json
import unittest
from unittest.mock import PropertyMock, patch
from fzfaws.s3.helper.get_copy_args import get_copy_args, check_acl_update
from fzfaws.s3.helper.s3args import S3Args
from botocore.stub import Stubber
import boto3
from fzfaws.s3 import S3
from fzfaws.s3.helper.s3args import S3Args


class TestS3GetCopyArgs(unittest.TestCase):
    @patch.object(S3Args, "acl_full", new_callable=PropertyMock)
    @patch.object(S3Args, "acl_read", new_callable=PropertyMock)
    @patch.object(S3Args, "acl_acp_write", new_callable=PropertyMock)
    @patch.object(S3Args, "acl_acp_read", new_callable=PropertyMock)
    def test_check_acl_update(
        self, mocked_acp_read, mocked_acp_write, mocked_read, mocked_full
    ):
        mocked_read.return_value = True
        mocked_full.return_value = True
        mocked_acp_write.return_value = True
        mocked_acp_read.return_value = True
        s3_args = S3Args
        result = check_acl_update(s3_args)
        self.assertEqual(result, False)

        mocked_read.return_value = False
        mocked_full.return_value = True
        mocked_acp_write.return_value = True
        mocked_acp_read.return_value = True
        s3_args = S3Args
        result = check_acl_update(s3_args)
        self.assertEqual(result, False)

        mocked_read.return_value = False
        mocked_full.return_value = False
        mocked_acp_write.return_value = False
        mocked_acp_read.return_value = False
        s3_args = S3Args
        result = check_acl_update(s3_args)
        self.assertEqual(result, True)

    def test_get_copy_args_no_version(self):
        data_path1 = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/s3_obj.json"
        )
        with open(data_path1, "r") as file:
            response1 = json.load(file)
        data_path2 = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/s3_acl.json"
        )
        with open(data_path2, "r") as file:
            response2 = json.load(file)

        # no version, update acl true
        s3_client = boto3.client("s3")
        stubber = Stubber(s3_client)
        stubber.add_response("get_object", response1)
        stubber.add_response("get_object_acl", response2)
        stubber.activate()
        s3 = S3()
        s3._client = s3_client
        s3.bucket_name = "hello"
        s3_args = S3Args(s3)
        result = get_copy_args(s3, "hello.json", s3_args, False)
        self.assertEqual(
            result,
            {
                "Bucket": "hello",
                "Key": "hello.json",
                "CopySource": {"Bucket": "hello", "Key": "hello.json"},
                "StorageClass": "REDUCED_REDUNDANCY",
                "ServerSideEncryption": "aws:kms",
                "SSEKMSKeyId": "arn:aws:kms:ap-southeast-2:11111111:key/11111111-f48d-48b8-90d4-d5bd03a603d4",
                "GrantRead": "uri=http://acs.amazonaws.com/groups/global/AllUsers",
            },
        )

        # no version, update acl false
        s3_client = boto3.client("s3")
        stubber = Stubber(s3_client)
        stubber.add_response("get_object", response1)
        stubber.add_response("get_object_acl", response2)
        stubber.activate()
        s3 = S3()
        s3._client = s3_client
        s3.bucket_name = "hello"
        s3_args = S3Args(s3)
        s3_args._extra_args["GrantFullControl"] = "email=hello@gmail.com"
        result = get_copy_args(s3, "hello.json", s3_args, False)
        self.assertEqual(
            result,
            {
                "Bucket": "hello",
                "Key": "hello.json",
                "CopySource": {"Bucket": "hello", "Key": "hello.json"},
                "GrantFullControl": "email=hello@gmail.com",
                "StorageClass": "REDUCED_REDUNDANCY",
                "ServerSideEncryption": "aws:kms",
                "SSEKMSKeyId": "arn:aws:kms:ap-southeast-2:11111111:key/11111111-f48d-48b8-90d4-d5bd03a603d4",
            },
        )

        # no version, no extra_args
        s3_client = boto3.client("s3")
        stubber = Stubber(s3_client)
        stubber.add_response("get_object", response1)
        stubber.add_response("get_object_acl", response2)
        stubber.activate()
        s3 = S3()
        s3._client = s3_client
        s3.bucket_name = "hello"
        s3_args = S3Args(s3)
        s3_args._extra_args["GrantFullControl"] = "email=hello@gmail.com"
        result = get_copy_args(s3, "hello.json", s3_args, True)
        self.assertEqual(
            result,
            {
                "GrantFullControl": "email=hello@gmail.com",
                "StorageClass": "REDUCED_REDUNDANCY",
                "ServerSideEncryption": "aws:kms",
                "SSEKMSKeyId": "arn:aws:kms:ap-southeast-2:11111111:key/11111111-f48d-48b8-90d4-d5bd03a603d4",
            },
        )

    def test_get_copy_args_with_version(self):
        data_path1 = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/s3_obj.json"
        )
        with open(data_path1, "r") as file:
            response1 = json.load(file)
        data_path2 = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/s3_acl.json"
        )
        with open(data_path2, "r") as file:
            response2 = json.load(file)

        # with version
        s3_client = boto3.client("s3")
        stubber = Stubber(s3_client)
        stubber.add_response("get_object", response1)
        stubber.add_response("get_object_acl", response2)
        stubber.activate()
        s3 = S3()
        s3._client = s3_client
        s3.bucket_name = "hello"
        s3_args = S3Args(s3)
        result = get_copy_args(s3, "hello.json", s3_args, False)
        self.assertEqual(
            result,
            {
                "Bucket": "hello",
                "Key": "hello.json",
                "CopySource": {"Bucket": "hello", "Key": "hello.json"},
                "StorageClass": "REDUCED_REDUNDANCY",
                "ServerSideEncryption": "aws:kms",
                "SSEKMSKeyId": "arn:aws:kms:ap-southeast-2:11111111:key/11111111-f48d-48b8-90d4-d5bd03a603d4",
                "GrantRead": "uri=http://acs.amazonaws.com/groups/global/AllUsers",
            },
        )
