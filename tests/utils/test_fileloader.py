import os
import json
import unittest
import tempfile
from unittest.mock import patch
from fzfaws.utils import FileLoader


class TestFileLoader(unittest.TestCase):
    def setUp(self):
        self.fileloader = FileLoader()
        curr_path = os.path.dirname(os.path.abspath(__file__))
        self.test_json = tempfile.NamedTemporaryFile()
        with open(self.test_json.name, "w") as file:
            file.write(json.dumps({"hello": "world", "foo": "boo"}))
        self.test_yaml = os.path.join(curr_path, "../data/fzfaws.yml")

    def tearDown(self):
        # reset cloudformation profile/region to align with test config file
        os.environ["FZFAWS_CLOUDFORMATION_PROFILE"] = ""
        os.environ["FZFAWS_CLOUDFORMATION_REGION"] = ""
        # reload config file
        self.fileloader.load_config_file(config_path=self.test_yaml)

    def test_consctructor(self):
        self.assertEqual(self.fileloader.path, "")
        self.assertEqual(self.fileloader.body, "")

        fileloader = FileLoader(path=self.test_json.name)
        self.assertEqual(fileloader.path, self.test_json.name)
        self.assertEqual(fileloader.body, "")

    def test_process_yaml_file(self):
        self.fileloader.path = self.test_yaml
        result = self.fileloader.process_yaml_file()
        self.assertRegex(result["body"], r".*fzf:\n")
        if "executable" not in result["dictBody"]["fzf"]:
            self.fail("Yaml file is not read properly")

    def test_process_json_body(self):
        self.fileloader.path = self.test_json.name
        result = self.fileloader.process_json_file()
        self.assertRegex(result["body"], r".*hello.*foo")
        if "foo" not in result["dictBody"]:
            self.fail("Json file is not read properly")

    @patch.object(FileLoader, "_set_cloudformation_env")
    @patch.object(FileLoader, "_set_s3_env")
    @patch.object(FileLoader, "_set_ec2_env")
    @patch.object(FileLoader, "_set_gloable_env")
    @patch.object(FileLoader, "_set_fzf_env")
    def test_load_config_file(
        self,
        mocked_set_fzf,
        mocked_set_global,
        mocked_set_ec2,
        mocked_set_s3,
        mocked_set_cloudformation,
    ):
        self.fileloader.path = self.test_yaml
        self.fileloader.load_config_file(config_path=self.test_yaml)
        mocked_set_fzf.assert_called_once()
        mocked_set_global.assert_called_once()
        mocked_set_ec2.assert_called_once()
        mocked_set_s3.assert_called_once()
        mocked_set_cloudformation.assert_called_once()

    def test_set_cloudformation_env(self):
        # normal test
        self.fileloader.load_config_file(config_path=self.test_yaml)
        self.assertEqual(os.getenv("FZFAWS_CLOUDFORMATION_PROFILE", ""), "")
        self.assertEqual(os.getenv("FZFAWS_CLOUDFORMATION_REGION", ""), "")
        self.assertEqual(os.environ["FZFAWS_CLOUDFORMATION_CREATE"], "--wait --extra")
        self.assertEqual(os.environ["FZFAWS_CLOUDFORMATION_DELETE"], "--wait")
        self.assertEqual(os.environ["FZFAWS_CLOUDFORMATION_UPDATE"], "--wait --extra")
        self.assertEqual(
            os.environ["FZFAWS_CLOUDFORMATION_WAITER"],
            json.dumps({"delay": 30, "max_attempts": 120}),
        )

        # reset
        os.environ["FZFAWS_CLOUDFORMATION_CREATE"] = ""
        os.environ["FZFAWS_CLOUDFORMATION_DELETE"] = ""
        os.environ["FZFAWS_CLOUDFORMATION_UPDATE"] = ""
        os.environ["FZFAWS_CLOUDFORMATION_WAITER"] = ""

        # empty test
        self.fileloader._set_cloudformation_env({})
        self.assertEqual(os.getenv("FZFAWS_CLOUDFORMATION_PROFILE", ""), "")
        self.assertEqual(os.getenv("FZFAWS_CLOUDFORMATION_REGION", ""), "")
        self.assertEqual(os.environ["FZFAWS_CLOUDFORMATION_CREATE"], "")
        self.assertEqual(os.environ["FZFAWS_CLOUDFORMATION_DELETE"], "")
        self.assertEqual(os.environ["FZFAWS_CLOUDFORMATION_UPDATE"], "")
        self.assertEqual(os.environ["FZFAWS_CLOUDFORMATION_WAITER"], "")

        # custom settings
        self.fileloader._set_cloudformation_env(
            {"profile": "root", "region": "us-east-2", "default_args": {"create": "-l"}}
        )
        self.assertEqual(os.environ["FZFAWS_CLOUDFORMATION_PROFILE"], "root")
        self.assertEqual(os.environ["FZFAWS_CLOUDFORMATION_REGION"], "us-east-2")
        self.assertEqual(os.environ["FZFAWS_CLOUDFORMATION_CREATE"], "-l")

    def test_set_s3_env(self):
        # normal test
        self.fileloader.load_config_file(config_path=self.test_yaml)
        self.assertEqual(
            os.environ["FZFAWS_S3_TRANSFER"],
            json.dumps(
                {
                    "multipart_threshold": 8,
                    "multipart_chunksize": 8,
                    "max_concurrency": 10,
                    "max_io_queue": 100,
                    "num_download_attempts": 6,
                }
            ),
        )
        self.assertEqual(os.environ["FZFAWS_S3_PROFILE"], "default")
        self.assertEqual(os.environ["FZFAWS_S3_UPLOAD"], "--hidden")
        self.assertEqual(os.environ["FZFAWS_S3_DOWNLOAD"], "--hidden")
        self.assertEqual(os.environ["FZFAWS_S3_PRESIGN"], "-e 3600")
        self.assertEqual(os.getenv("FZFAWS_S3_LS", ""), "")

        # reset
        os.environ["FZFAWS_S3_TRANSFER"] = ""
        os.environ["FZFAWS_S3_PROFILE"] = ""
        os.environ["FZFAWS_S3_UPLOAD"] = ""
        os.environ["FZFAWS_S3_DOWNLOAD"] = ""
        os.environ["FZFAWS_S3_PRESIGN"] = ""

        # empty test
        self.fileloader._set_s3_env({})
        self.assertEqual(os.getenv("FZFAWS_S3_TRANSFER", ""), "")
        self.assertEqual(os.getenv("FZFAWS_S3_PROFILE", ""), "")
        self.assertEqual(os.getenv("FZFAWS_S3_UPLOAD", ""), "")
        self.assertEqual(os.getenv("FZFAWS_S3_DOWNLOAD", ""), "")
        self.assertEqual(os.getenv("FZFAWS_S3_PRESIGN", ""), "")

        # custom settings
        self.fileloader._set_s3_env(
            {
                "transfer_config": {"multipart_threshold": 1, "multipart_chunksize": 1},
                "profile": "root",
                "default_args": {"upload": "-R", "ls": "-b"},
            }
        )
        self.assertEqual(
            os.environ["FZFAWS_S3_TRANSFER"],
            json.dumps({"multipart_threshold": 1, "multipart_chunksize": 1,}),
        )
        self.assertEqual(os.environ["FZFAWS_S3_UPLOAD"], "-R")
        self.assertEqual(os.environ["FZFAWS_S3_PROFILE"], "root")
        self.assertEqual(os.environ["FZFAWS_S3_LS"], "-b")
        self.assertEqual(os.getenv("FZFAWS_S3_DOWNLOAD", ""), "")
        self.assertEqual(os.getenv("FZFAWS_S3_PRESIGN", ""), "")

    def test_set_ec2_env(self):
        # normal test
        self.fileloader.load_config_file(config_path=self.test_yaml)
        self.assertEqual(os.environ["FZFAWS_EC2_KEYPAIRS"], "~/.ssh")
        self.assertEqual(
            os.environ["FZFAWS_EC2_WAITER"],
            json.dumps({"delay": 10, "max_attempts": 60}),
        )
        self.assertEqual(os.environ["FZFAWS_EC2_START"], "--wait")
        self.assertEqual(os.environ["FZFAWS_EC2_STOP"], "--wait")
        self.assertEqual(os.environ["FZFAWS_EC2_REGION"], "us-east-1")
        self.assertEqual(os.environ["FZFAWS_EC2_PROFILE"], "default")

        # reset
        os.environ["FZFAWS_EC2_WAITER"] = ""
        os.environ["FZFAWS_EC2_KEYPAIRS"] = ""
        os.environ["FZFAWS_EC2_START"] = ""
        os.environ["FZFAWS_EC2_STOP"] = ""
        os.environ["FZFAWS_EC2_PROFILE"] = ""
        os.environ["FZFAWS_EC2_REGION"] = ""

        # empty test
        self.fileloader._set_ec2_env({})
        self.assertEqual(os.getenv("FZFAWS_EC2_WAITER", ""), "")
        self.assertEqual(os.getenv("FZFAWS_EC2_START", ""), "")
        self.assertEqual(os.getenv("FZFAWS_EC2_STOP", ""), "")
        self.assertEqual(os.getenv("FZFAWS_EC2_KEYPAIRS", ""), "")
        self.assertEqual(os.getenv("FZFAWS_EC2_REGION", ""), "")
        self.assertEqual(os.getenv("FZFAWS_EC2_PROFILE", ""), "")

        # custom settings
        self.fileloader._set_ec2_env(
            {
                "keypair": "$HOME/Anywhere/aws",
                "waiter": {"max_attempts": 40},
                "default_args": {"ssh": "-A"},
                "region": "us-east-1",
                "profile": "root",
            }
        )
        self.assertEqual(os.environ["FZFAWS_EC2_KEYPAIRS"], "$HOME/Anywhere/aws")
        self.assertEqual(
            os.environ["FZFAWS_EC2_WAITER"], json.dumps({"max_attempts": 40}),
        )
        self.assertEqual(os.environ["FZFAWS_EC2_SSH"], "-A")
        self.assertEqual(os.environ["FZFAWS_EC2_REGION"], "us-east-1")
        self.assertEqual(os.environ["FZFAWS_EC2_PROFILE"], "root")

    def test_set_global_env(self):
        # normal test
        self.fileloader.load_config_file(config_path=self.test_yaml)
        self.assertEqual(
            os.environ["FZFAWS_GLOBAL_WAITER"],
            json.dumps({"delay": 15, "max_attempts": 40}),
        )
        self.assertEqual(os.environ["FZFAWS_GLOBAL_REGION"], "us-east-1")
        self.assertEqual(os.environ["FZFAWS_GLOBAL_PROFILE"], "default")

        # reset
        os.environ["FZFAWS_GLOBAL_WAITER"] = ""
        os.environ["FZFAWS_GLOBAL_PROFILE"] = ""
        os.environ["FZFAWS_GLOBAL_REGION"] = ""

        # empty test
        self.fileloader._set_gloable_env({})
        self.assertEqual(os.getenv("FZFAWS_GLOBAL_WAITER", ""), "")
        self.assertEqual(os.environ["FZFAWS_GLOBAL_REGION"], "")
        self.assertEqual(os.environ["FZFAWS_GLOBAL_PROFILE"], "")

        # custom settings
        self.fileloader._set_gloable_env(
            {"profile": "root", "region": "us-east-1", "waiter": {"delay": 10}}
        )
        self.assertEqual(os.environ["FZFAWS_GLOBAL_WAITER"], json.dumps({"delay": 10}))
        self.assertEqual(os.environ["FZFAWS_GLOBAL_REGION"], "us-east-1")
        self.assertEqual(os.environ["FZFAWS_GLOBAL_PROFILE"], "root")

        os.environ["FZFAWS_GLOBAL_WAITER"] = ""
        self.fileloader._set_gloable_env({"profile": "root", "region": "us-east-1"})
        self.assertEqual(os.environ["FZFAWS_GLOBAL_WAITER"], "")
        self.assertEqual(os.environ["FZFAWS_GLOBAL_REGION"], "us-east-1")
        self.assertEqual(os.environ["FZFAWS_GLOBAL_PROFILE"], "root")

    def test_set_fzf_env(self):
        # normal test
        self.fileloader.load_config_file(config_path=self.test_yaml)
        self.assertEqual(os.environ["FZFAWS_FZF_EXECUTABLE"], "binary")
        self.assertEqual(
            os.environ["FZFAWS_FZF_KEYS"],
            "--bind=alt-a:toggle-all,alt-j:jump,alt-0:top,alt-s:toggle-sort",
        )

        self.assertRegex(os.environ["FZFAWS_FZF_OPTS"], r"^--color=dark\s--color=.*")

        # reset
        os.environ["FZFAWS_FZF_EXECUTABLE"] = ""
        os.environ["FZFAWS_FZF_OPTS"] = ""
        os.environ["FZFAWS_FZF_KEYS"] = ""

        # empty test
        self.fileloader._set_fzf_env({})
        self.assertEqual(os.getenv("FZFAWS_FZF_KEYS", ""), "")
        self.assertEqual(os.getenv("FZFAWS_FZF_EXECUTABLE", ""), "")
        self.assertEqual(os.getenv("FZFAWS_FZF_OPTS", ""), "")

        # custom settings
        self.fileloader._set_fzf_env(
            {"executable": "system", "args": "hello", "keybinds": {"foo": "boo"}}
        )
        self.assertEqual(os.environ["FZFAWS_FZF_KEYS"], "--bind=boo:foo")
        self.assertEqual(os.environ["FZFAWS_FZF_OPTS"], "hello")
        self.assertEqual(os.environ["FZFAWS_FZF_EXECUTABLE"], "system")

    def test_set_spinner_env(self):
        self.fileloader.load_config_file(config_path=self.test_yaml)
        self.assertEqual(os.environ["FZFAWS_SPINNER_SPEED"], "0.1")
        self.assertEqual(os.environ["FZFAWS_SPINNER_MESSAGE"], "loading ...")
        self.assertEqual(os.environ["FZFAWS_SPINNER_PATTERN"], "|/-\\")

        # reset
        os.environ["FZFAWS_SPINNER_PATTERN"] = ""
        os.environ["FZFAWS_SPINNER_MESSAGE"] = ""
        os.environ["FZFAWS_SPINNER_SPEED"] = ""

        # empty test
        self.fileloader._set_spinner_env({})
        self.assertEqual(os.getenv("FZFAWS_SPINNER_SPEED", ""), "")
        self.assertEqual(os.getenv("FZFAWS_SPINNER_MESSAGE", ""), "")
        self.assertEqual(os.getenv("FZFAWS_SPINNER_PATTERN", ""), "")

        # custom settings
        self.fileloader._set_spinner_env(
            {"message": "hello", "speed": "0.8", "pattern": "xxx"}
        )
        self.assertEqual(os.environ["FZFAWS_SPINNER_SPEED"], "0.8")
        self.assertEqual(os.environ["FZFAWS_SPINNER_MESSAGE"], "hello")
        self.assertEqual(os.environ["FZFAWS_SPINNER_PATTERN"], "xxx")
