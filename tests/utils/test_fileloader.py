import os
import json
import unittest
from fzfaws.utils import FileLoader


class TestFileLoader(unittest.TestCase):
    def setUp(self):
        self.fileloader = FileLoader()
        full_path = os.path.abspath(__file__)
        path, filename = os.path.split(full_path)
        self.test_json = "%s/test.json" % path
        with open(self.test_json, "w") as file:
            file.write(json.dumps({"hello": "world", "foo": "boo"}))
        self.test_yaml = "%s/../../fzfaws.yml" % path

    def tearDown(self):
        os.remove(self.test_json)
        os.environ["FZFAWS_FZF_EXECUTABLE"] = "binary"
        os.environ["FZFAWS_FZF_OPTS"] = ""
        os.environ["FZFAWS_FZF_KEYS"] = ""

    def test_consctructor(self):
        self.assertEqual(self.fileloader.path, "")
        self.assertEqual(self.fileloader.body, "")

        fileloader = FileLoader(path=self.test_json)
        self.assertEqual(fileloader.path, self.test_json)
        self.assertEqual(fileloader.body, "")

    def test_process_yaml_file(self):
        self.fileloader.path = self.test_yaml
        result = self.fileloader.process_yaml_file()
        self.assertRegex(result["body"], r".*fzf:\n")
        if "executable" not in result["dictBody"]["fzf"]:
            self.fail("Yaml file is not read properly")

    def test_process_json_body(self):
        self.fileloader.path = self.test_json
        result = self.fileloader.process_json_file()
        self.assertRegex(result["body"], r".*hello.*foo")
        if "foo" not in result["dictBody"]:
            self.fail("Json file is not read properly")

    def test_load_config_file(self):
        self.fileloader.path = self.test_yaml
        self.fileloader.load_config_file(config_path=self.test_yaml)
        self.assertEqual(os.environ["FZFAWS_FZF_EXECUTABLE"], "binary")
        self.assertEqual(
            os.environ["FZFAWS_FZF_KEYS"],
            "--bind=alt-a:toggle-all,alt-j:jump,alt-0:top,alt-s:toggle-sort",
        )
        self.assertRegex(os.environ["FZFAWS_FZF_OPTS"], r"^--color=dark\s--color=.*")

        os.environ["FZFAWS_FZF_EXECUTABLE"] = ""
        os.environ["FZFAWS_FZF_OPTS"] = ""
        os.environ["FZFAWS_FZF_KEYS"] = ""
        self.fileloader._set_fzf_env({"executable": "system"})
        self.assertEqual(os.getenv("FZFAWS_FZF_KEYS", ""), "")
        self.assertEqual(os.getenv("FZFAWS_FZF_EXECUTABLE"), "system")
        self.assertEqual(os.getenv("FZFAWS_FZF_OPTS", ""), "")

    def test_set_fzf_env(self):
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
