import unittest
import subprocess
import io
import sys
from unittest.mock import patch
from fzfaws.utils import Pyfzf
from fzfaws.utils.exceptions import NoSelectionMade


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

    @patch.object(Pyfzf, "_check_ctrl_c")
    @patch.object(subprocess, "check_output")
    def test_execute_fzf(self, mocked_output, mocked_ctrlc):
        mocked_ctrlc.return_value = None
        mocked_output.return_value = b"hello"
        result = self.fzf.execute_fzf()
        self.assertEqual(result, "hello")

        mocked_output.return_value = b""
        self.assertRaises(NoSelectionMade, self.fzf.execute_fzf)

        mocked_output.return_value = b""
        result = self.fzf.execute_fzf(empty_allow=True)
        self.assertEqual("", result)

    @patch.object(subprocess, "check_output")
    def test_check_ctrl_c(self, mocked_output):
        mocked_output.return_value = b"ctrl-c"
        self.assertRaises(KeyboardInterrupt, self.fzf.execute_fzf)
        mocked_output.return_value = b"hello"
        try:
            self.fzf.execute_fzf()
        except:
            self.fail("ctrl-c test failed, unexpected exception raise")
