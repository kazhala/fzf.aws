import unittest

from fzfaws.cloudformation.helper.file_validation import (
    check_is_valid,
    is_json,
    is_yaml,
)
from fzfaws.utils.exceptions import InvalidFileType


class TestCloudformationFileValidation(unittest.TestCase):
    def test_is_yaml(self):
        result = is_yaml("hello.json")
        self.assertEqual(result, False)

        result = is_yaml("hello.yaml")
        self.assertEqual(result, True)

        result = is_yaml("hello.yml")
        self.assertEqual(result, True)

    def test_is_json(self):
        result = is_json("hello.json")
        self.assertEqual(result, True)

        result = is_json("hello.yml")
        self.assertEqual(result, False)

    def test_check_is_valid(self):
        check_is_valid("hello.yaml")
        check_is_valid("hello.json")
        check_is_valid("hello.yml")
        self.assertRaises(InvalidFileType, check_is_valid, "hello.txt")
