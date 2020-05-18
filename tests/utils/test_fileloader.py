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
        self.fileloader.load_config_file()
        self.assertEqual(os.environ["FZFAWS_FZF_EXECUTABLE"], "binary")
        self.assertEqual(
            os.environ["FZFAWS_FZF_KEYS"],
            "--bind=alt-a:toggle-all,alt-j:jump,alt-0:top,alt-s:toggle-sort",
        )
