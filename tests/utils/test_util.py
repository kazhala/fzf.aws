import unittest
from unittest.mock import patch
from fzfaws.utils.util import (
    check_dict_value_in_list,
    remove_dict_from_list,
    search_dict_in_list,
)


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
