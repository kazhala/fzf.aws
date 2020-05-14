import unittest
import subprocess
import io
import sys
from unittest.mock import patch
from fzfaws.utils import Pyfzf
from fzfaws.utils.exceptions import EmptyList, NoSelectionMade


class TestPyfzf(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput
        self.fzf = Pyfzf()

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_constructor(self):
        self.assertRegex(
            self.fzf.fzf_path,
            r".*fzf.aws/fzfaws.*/libs/fzf-[0-9]\.[0-9]+\.[0-9]-(linux|darwin)_(386|amd64)",
        )
        self.assertEqual("", self.fzf.fzf_string)

    def test_append_fzf(self):
        self.fzf.append_fzf("hello\n")
        self.fzf.append_fzf("world\n")
        self.assertEqual("hello\nworld\n", self.fzf.fzf_string)

    @patch.object(subprocess, "Popen")
    @patch.object(subprocess, "check_output")
    def test_execute_fzf(self, mocked_output, mocked_popen):
        mocked_output.return_value = b"hello"
        result = self.fzf.execute_fzf()
        self.assertEqual(result, "hello")
        self.assertEqual(mocked_output.call_count, 3)

        mocked_output.return_value = b""
        self.assertRaises(NoSelectionMade, self.fzf.execute_fzf)

        mocked_output.return_value = b""
        result = self.fzf.execute_fzf(empty_allow=True)
        self.assertEqual("", result)

        mocked_output.return_value = b"hello"
        result = self.fzf.execute_fzf(multi_select=True)
        self.assertEqual(result, ["hello"])

        mocked_output.return_value = b"hello\nworld"
        result = self.fzf.execute_fzf(multi_select=True)
        self.assertEqual(result, ["hello", "world"])

    @patch.object(subprocess, "Popen")
    @patch.object(subprocess, "check_output")
    def test_check_ctrl_c(self, mocked_output, mocked_popen):
        mocked_output.return_value = b"ctrl-c"
        self.assertRaises(KeyboardInterrupt, self.fzf.execute_fzf)
        mocked_output.return_value = b"hello"
        try:
            self.fzf.execute_fzf()
        except:
            self.fail("ctrl-c test failed, unexpected exception raise")

    @patch.object(subprocess, "Popen")
    @patch.object(subprocess, "check_output")
    def test_get_local_file(self, mocked_output, mocked_popen):
        mocked_output.return_value = b""
        self.assertRaises(NoSelectionMade, self.fzf.get_local_file)

        mocked_output.return_value = b"hello"
        result = self.fzf.get_local_file()
        self.assertEqual("hello", result)

        mocked_output.return_value = b"hello"
        result = self.fzf.get_local_file(multi_select=True)
        self.assertEqual(result, ["hello"])

        mocked_output.return_value = b"hello\nworld\n"
        result = self.fzf.get_local_file(multi_select=True)
        self.assertEqual(result, ["hello", "world"])

    @patch.object(subprocess, "Popen")
    def test_check_fd(self, mocked_popen):
        result = self.fzf._check_fd()
        self.assertEqual(type(result), bool)

    def test_process_list(self):
        self.fzf.fzf_string = ""
        self.assertRaises(EmptyList, self.fzf.process_list, [], "123")

        test_list = [{"foo": 1, "boo": 2}, {"foo": "b"}]
        self.fzf.process_list(test_list, "foo")
        self.assertEqual(self.fzf.fzf_string, "foo: 1\nfoo: b\n")

        self.fzf.fzf_string = ""
        self.fzf.process_list(test_list, "boo")
        self.assertEqual(self.fzf.fzf_string, "boo: 2\nboo: N/A\n")

        self.fzf.fzf_string = ""
        self.fzf.process_list(test_list, "www")
        self.assertEqual(self.fzf.fzf_string, "www: N/A\nwww: N/A\n")
