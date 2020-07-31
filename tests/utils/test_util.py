import os
import json
import unittest
from unittest.mock import patch
from fzfaws.utils import (
    check_dict_value_in_list,
    get_confirmation,
    remove_dict_from_list,
    search_dict_in_list,
    get_name_tag,
    get_default_args,
    FileLoader,
)
from pathlib import Path


class TestUtil(unittest.TestCase):
    def test_remove_dict_from_list(self):
        test_list = [{"hello": "world"}, {"hello": "no"}]
        test_list = remove_dict_from_list("no", test_list, "hello")
        self.assertEqual(test_list, [{"hello": "world"}])
        test_list = remove_dict_from_list("afasdfa", test_list, "bbbb")
        self.assertEqual(test_list, [{"hello": "world"}])

    def test_search_dict_in_list(self):
        test_list = [{"hello": "world"}, {"hello": "no"}]
        result = search_dict_in_list("no", test_list, "hello")
        self.assertEqual(result, {"hello": "no"})
        result = search_dict_in_list("asdf", test_list, "asdfa")
        self.assertEqual(result, {})
        test_list = []
        result = search_dict_in_list("no", test_list, "hello")
        self.assertEqual(result, {})

    def test_check_dict_value_in_list(self):
        test_list = [{"hello": "world"}, {"hello": "no"}]
        result = check_dict_value_in_list("world", test_list, "hello")
        self.assertTrue(result)
        result = check_dict_value_in_list("yes", test_list, "yes")
        self.assertFalse(result)
        test_list = []
        result = check_dict_value_in_list("yes", test_list, "yes")
        self.assertFalse(result)

    @patch("fzfaws.utils.util.prompt")
    def test_get_confirmation(self, mocked_prompt):
        mocked_prompt.return_value = {"continue": True}
        response = get_confirmation("Confirm?")
        self.assertTrue(response)

        mocked_prompt.return_value = {"continue": False}
        response = get_confirmation("Confirm?")
        self.assertFalse(response)

    def test_get_name_tag(self):
        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/ec2_instance.json"
        )
        with open(data_path, "r") as file:
            test_data = json.load(file)

        name = get_name_tag(test_data[0]["Reservations"][0]["Instances"][0])
        self.assertEqual(name, "meal-Bean-10PYXE0G1F4HS")
        test_data = {}
        name = get_name_tag(test_data)
        self.assertEqual(name, None)

    def test_get_default_args(self):
        fileloader = FileLoader()
        config_path = Path(__file__).resolve().parent.joinpath("../data/fzfaws.yml")
        fileloader.load_config_file(config_path=str(config_path))
        result = get_default_args("ec2", ["start", "-e", "-m"])
        self.assertEqual(result, ["start", "--wait", "-e", "-m"])

        result = get_default_args("s3", ["upload", "-b", "-x"])
        self.assertEqual(result, ["upload", "--hidden", "-b", "-x"])

        result = get_default_args("s3", ["presign"])
        self.assertEqual(result, ["presign", "-e", "3600"])

        result = get_default_args("ec2", [])
        self.assertEqual(result, [])

        result = get_default_args("ec2", ["ls"])
        self.assertEqual(result, ["ls"])
