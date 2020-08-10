from fzfaws.utils.util import CommaListValidator, URLQueryStringValidator, prompt_style
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.session import BaseSession
import io
import json
import os
import sys
import unittest
from unittest.mock import ANY, PropertyMock, patch
from fzfaws.s3.helper.s3args import S3Args
from fzfaws.s3 import S3
import boto3
from botocore.stub import Stubber
from fzfaws.kms import KMS
from pathlib import Path


class TestS3Args(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput
        s3 = S3()
        s3.bucket_name = "hello"
        s3.path_list = ["hello.json"]
        self.s3_args = S3Args(s3)

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_constructor(self):
        self.assertIsInstance(self.s3_args.s3, S3)
        self.assertEqual(self.s3_args._extra_args, {})

    @patch("fzfaws.s3.helper.s3args.prompt")
    @patch.object(S3Args, "set_tags")
    @patch.object(S3Args, "set_metadata")
    @patch.object(S3Args, "set_encryption")
    @patch.object(S3Args, "set_ACL")
    @patch.object(S3Args, "set_storageclass")
    @patch.object(BaseSession, "resource", new_callable=PropertyMock)
    def test_set_extra_args(
        self,
        mocked_resource,
        mocked_storage,
        mocked_acl,
        mocked_encryption,
        mocked_metadata,
        mocked_tags,
        mocked_prompt,
    ):
        data_path = Path(__file__).resolve().parent.joinpath("../data/s3_obj.json")
        with data_path.open("r") as file:
            response = json.load(file)

        # normal no version test
        s3 = boto3.resource("s3")
        stubber = Stubber(s3.meta.client)
        stubber.add_response("get_object", response)
        stubber.activate()
        mocked_prompt.return_value = {
            "selected_attributes": [
                "StorageClass",
                "ACL",
                "Metadata",
                "Encryption",
                "Tagging",
            ]
        }

        self.s3_args.set_extra_args()
        mocked_prompt.assert_called_once_with(
            [
                {
                    "type": "checkbox",
                    "name": "selected_attributes",
                    "message": "Select attributes to configure",
                    "choices": [
                        {"name": "StorageClass"},
                        {"name": "ACL"},
                        {"name": "Encryption"},
                        {"name": "Metadata"},
                        {"name": "Tagging"},
                    ],
                }
            ],
            style=prompt_style,
        )
        mocked_storage.assert_called()
        mocked_acl.assert_called_with(original=True, version=[])
        mocked_encryption.assert_called()
        mocked_metadata.assert_called()
        mocked_tags.assert_called_with(original=True, version=[])

        # normal no call no version test
        mocked_encryption.reset_mock()
        mocked_prompt.reset_mock()
        mocked_tags.reset_mock()
        mocked_tags.reset_mock()
        mocked_metadata.reset_mock()
        mocked_storage.reset_mock()
        mocked_acl.reset_mock()
        s3 = boto3.resource("s3")
        stubber = Stubber(s3.meta.client)
        stubber.add_response("get_object", response)
        stubber.activate()
        self.s3_args.set_extra_args(storage=True, upload=True)
        mocked_storage.assert_called()
        mocked_prompt.assert_not_called()
        mocked_tags.assert_not_called()
        mocked_tags.assert_not_called()
        mocked_metadata.assert_not_called()
        mocked_acl.assert_not_called()
        mocked_encryption.assert_not_called()

        # version test
        mocked_encryption.reset_mock()
        mocked_prompt.reset_mock()
        mocked_tags.reset_mock()
        mocked_tags.reset_mock()
        mocked_metadata.reset_mock()
        mocked_storage.reset_mock()
        mocked_acl.reset_mock()
        s3 = boto3.resource("s3")
        stubber = Stubber(s3.meta.client)
        stubber.add_response("get_object", response)
        stubber.activate()
        mocked_prompt.return_value = {"selected_attributes": ["ACL", "Tagging"]}
        self.s3_args.set_extra_args(
            version=[{"Key": "hello.json", "VersionId": "11111111"}]
        )
        mocked_storage.assert_not_called()
        mocked_acl.assert_called_with(
            original=True, version=[{"Key": "hello.json", "VersionId": "11111111"}]
        )
        mocked_encryption.assert_not_called()
        mocked_metadata.assert_not_called()
        mocked_tags.assert_called_with(
            original=True, version=[{"Key": "hello.json", "VersionId": "11111111"}]
        )

    @patch("fzfaws.s3.helper.s3args.prompt")
    def test_set_metadata(self, mocked_prompt):
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        self.s3_args._extra_args = {}
        mocked_prompt.return_value = {"metadata": "foo=boo"}
        self.s3_args.set_metadata(original="hello")
        self.assertEqual(self.s3_args._extra_args, {"Metadata": {"foo": "boo"}})
        mocked_prompt.assert_called_once_with(
            [
                {
                    "type": "input",
                    "name": "metadata",
                    "message": "Metadata",
                    "validate": URLQueryStringValidator,
                    "default": "hello",
                }
            ],
            style=prompt_style,
        )

        mocked_prompt.return_value = {"metadata": "foo=boo&hello=world&"}
        self.s3_args.set_metadata()
        self.assertEqual(
            self.s3_args._extra_args, {"Metadata": {"foo": "boo", "hello": "world"}}
        )

    @patch("fzfaws.s3.helper.s3args.prompt")
    def test_set_storageclass(self, mocked_prompt):
        self.s3_args._extra_args = {}
        mocked_prompt.return_value = {"selected_class": "STANDARD"}
        self.s3_args.set_storageclass(original="GLACIER")
        mocked_prompt.assert_called_once_with(
            [
                {
                    "type": "rawlist",
                    "name": "selected_class",
                    "message": "Select a storage class (Original: GLACIER)",
                    "choices": [
                        "STANDARD",
                        "REDUCED_REDUNDANCY",
                        "STANDARD_IA",
                        "ONEZONE_IA",
                        "INTELLIGENT_TIERING",
                        "GLACIER",
                        "DEEP_ARCHIVE",
                    ],
                }
            ],
            style=prompt_style,
        )
        self.assertEqual(self.s3_args._extra_args, {"StorageClass": "STANDARD"})

        mocked_prompt.return_value = {"selected_class": "REDUCED_REDUNDANCY"}
        self.s3_args.set_storageclass()
        self.assertEqual(
            self.s3_args._extra_args, {"StorageClass": "REDUCED_REDUNDANCY"}
        )

    @patch("fzfaws.s3.helper.s3args.prompt")
    @patch.object(S3Args, "_set_explicit_ACL")
    @patch.object(S3Args, "_set_canned_ACL")
    def test_set_ACL(self, mocked_canned, mocked_explicit, mocked_prompt):
        mocked_prompt.return_value = {"selected_acl": "None"}
        self.s3_args.set_ACL()
        mocked_canned.assert_not_called()
        mocked_explicit.assert_not_called()
        mocked_prompt.assert_called_once_with(
            [
                {
                    "type": "rawlist",
                    "name": "selected_acl",
                    "message": "Select a type of ACL to grant, aws accept either canned ACL or explicit ACL",
                    "choices": [
                        "None: use bucket default ACL setting",
                        "Canned ACL: select predefined set of grantees and permissions",
                        "Explicit ACL: explicitly define grantees and permissions",
                    ],
                    "filter": ANY,
                }
            ],
            style=ANY,
        )

        mocked_prompt.return_value = {"selected_acl": "Canned"}
        self.s3_args.set_ACL(
            original=True, version=[{"Key": "hello.json", "VersionId": "11111111"}]
        )
        mocked_canned.assert_called_once()
        mocked_explicit.assert_not_called()

        mocked_canned.reset_mock()
        mocked_prompt.return_value = {"selected_acl": "Explicit"}
        self.s3_args.set_ACL(
            original=True, version=[{"Key": "hello.json", "VersionId": "11111111"}]
        )
        mocked_canned.assert_not_called()
        mocked_explicit.assert_called_with(
            original=True, version=[{"Key": "hello.json", "VersionId": "11111111"}]
        )

    @patch("fzfaws.s3.helper.s3args.prompt")
    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    @patch("fzfaws.s3.helper.s3args.get_confirmation")
    def test_set_explicit_ACL(self, mocked_confirm, mocked_client, mocked_prompt):
        data_path = Path(__file__).resolve().parent.joinpath("../data/s3_acl.json")
        with data_path.open("r") as file:
            response = json.load(file)

        # test orignal values
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        s3 = boto3.client("s3")
        stubber = Stubber(s3)
        stubber.add_response("get_object_acl", response)
        stubber.activate()
        mocked_confirm.return_value = False
        mocked_client.return_value = s3
        self.s3_args._set_explicit_ACL(
            original=True, version=[{"Key": "hello", "VersionId": "11111111"}]
        )
        self.assertRegex(
            self.capturedOutput.getvalue(),
            r".*uri=http://acs.amazonaws.com/groups/global/AllUsers",
        )

        # test no original value, set permissions
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        s3 = boto3.client("s3")
        stubber = Stubber(s3)
        stubber.add_response("get_object_acl", response)
        stubber.activate()
        mocked_client.return_value = s3
        mocked_prompt.return_value = {"selected_acl": ["GrantFullControl", "GrantRead"]}
        self.s3_args._set_explicit_ACL()

        self.assertEqual(
            self.s3_args._extra_args["GrantFullControl"], "",
        )
        self.assertEqual(
            self.s3_args._extra_args["GrantRead"], "",
        )
        mocked_prompt.assert_called_with(
            [
                {
                    "type": "input",
                    "name": "input_acl",
                    "message": "GrantRead",
                    "validate": CommaListValidator,
                }
            ],
            style=prompt_style,
        )

        # test original value, set permissions
        mocked_prompt.reset_mock()
        s3 = boto3.client("s3")
        stubber = Stubber(s3)
        stubber.add_response("get_object_acl", response)
        stubber.activate()
        mocked_client.return_value = s3
        mocked_prompt.return_value = {"selected_acl": "GrantRead"}
        mocked_confirm.return_value = True
        self.s3_args._set_explicit_ACL(original=True)
        self.assertEqual(
            self.s3_args._extra_args["GrantRead"], "",
        )

    @patch("fzfaws.s3.helper.s3args.prompt")
    def test_set_canned_ACL(self, mocked_prompt):
        mocked_prompt.return_value = {"selected_acl": "private"}
        self.s3_args._set_canned_ACL()
        self.assertEqual(self.s3_args._extra_args["ACL"], "private")
        mocked_prompt.assert_called_once_with(
            [
                {
                    "type": "rawlist",
                    "name": "selected_acl",
                    "message": "Select a Canned ACL option",
                    "choices": [
                        "private",
                        "public-read",
                        "public-read-write",
                        "authenticated-read",
                        "aws-exec-read",
                        "bucket-owner-read",
                        "bucket-owner-full-control",
                    ],
                }
            ],
            style=prompt_style,
        )

        self.s3_args._extra_args["ACL"] = None
        mocked_prompt.return_value = {}
        self.assertRaises(KeyboardInterrupt, self.s3_args._set_canned_ACL)

    @patch("fzfaws.s3.helper.s3args.prompt")
    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    @patch.object(KMS, "set_keyids")
    def test_encryption(self, mocked_kms, mocked_client, mocked_prompt):
        mocked_prompt.return_value = {"selected_encryption": "None"}
        self.s3_args.set_encryption(original="AES256")
        self.assertEqual(self.s3_args._extra_args["ServerSideEncryption"], "None")
        mocked_prompt(
            [
                {
                    "type": "rawlist",
                    "name": "selected_encryption",
                    "message": "select an encryption setting (Original: AES256)",
                    "choices": [
                        "None (Use bucket default setting)",
                        "AES256",
                        "aws:kms",
                    ],
                }
            ],
            style=ANY,
        )

        # test kms
        s3 = boto3.client("s3")
        stubber = Stubber(s3)
        stubber.add_response("get_bucket_location", {"LocationConstraint": "EU"})
        stubber.activate()
        mocked_client.return_value = s3

        mocked_prompt.return_value = {"selected_encryption": "aws:kms"}
        self.s3_args.set_encryption(original="AES256")
        self.assertEqual(self.s3_args._extra_args["ServerSideEncryption"], "aws:kms")
        self.assertEqual(self.s3_args._extra_args["SSEKMSKeyId"], "")

    @patch("fzfaws.s3.helper.s3args.prompt")
    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    def test_set_tags(self, mocked_client, mocked_prompt):
        mocked_prompt.return_value = {"answer": "hello=world"}
        self.s3_args.set_tags()
        self.assertEqual(self.s3_args._extra_args["Tagging"], "hello=world")

        data_path = Path(__file__).resolve().parent.joinpath("../data/s3_tags.json")
        with data_path.open("r") as file:
            response = json.load(file)
        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/s3_tags.json"
        )
        with open(data_path, "r") as file:
            response = json.load(file)

        mocked_prompt.reset_mock()
        s3 = boto3.client("s3")
        stubber = Stubber(s3)
        stubber.add_response("get_object_tagging", response)
        stubber.activate()
        mocked_client.return_value = s3
        mocked_prompt.return_value = {"answer": "foo=boo"}
        self.s3_args.set_tags(original=True)
        self.assertEqual(self.s3_args._extra_args["Tagging"], "foo=boo")
        mocked_prompt.assert_called_once_with(
            [
                {
                    "type": "input",
                    "name": "answer",
                    "message": "Tags",
                    "validate": URLQueryStringValidator,
                    "default": "name=yes",
                }
            ],
            style=prompt_style,
        )

        s3 = boto3.client("s3")
        stubber = Stubber(s3)
        stubber.add_response("get_object_tagging", response)
        stubber.activate()
        mocked_client.return_value = s3
        mocked_prompt.return_value = {"answer": "foo=boo"}
        self.s3_args.set_tags(
            original=True, version=[{"Key": "hello", "VersionId": "11111111"}]
        )
        self.assertEqual(self.s3_args._extra_args["Tagging"], "foo=boo")

    def test_check_tag_acl(self):
        self.s3_args._extra_args["StorageClass"] = "None"
        self.s3_args._extra_args["ServerSideEncryption"] = "None"
        self.s3_args._extra_args["Metadata"] = "hello=world"
        result = self.s3_args.check_tag_acl()
        self.assertEqual(result, {})

        self.s3_args._extra_args["StorageClass"] = ""
        self.s3_args._extra_args["ServerSideEncryption"] = ""
        self.s3_args._extra_args["Metadata"] = ""
        self.s3_args._extra_args["Tagging"] = "hello=world&foo=boo"
        self.s3_args._extra_args["ACL"] = "public-read"
        self.s3_args._extra_args["GrantFullControl"] = "id=11111111"
        self.s3_args._extra_args["GrantRead"] = "id=11111111"
        self.s3_args._extra_args["GrantReadACP"] = "id=11111111"
        self.s3_args._extra_args["GrantWriteACP"] = "id=11111111"
        result = self.s3_args.check_tag_acl()
        self.assertEqual(
            result,
            {
                "Grants": {
                    "ACL": "public-read",
                    "GrantFullControl": "id=11111111",
                    "GrantRead": "id=11111111",
                    "GrantReadACP": "id=11111111",
                    "GrantWriteACP": "id=11111111",
                },
                "Tags": [
                    {"Key": "hello", "Value": "world"},
                    {"Key": "foo", "Value": "boo"},
                ],
            },
        )
