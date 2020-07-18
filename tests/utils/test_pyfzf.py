import unittest
import subprocess
import io
import sys
import os
from unittest.mock import patch
from fzfaws.utils import Pyfzf, FileLoader
from fzfaws.utils.exceptions import EmptyList, NoSelectionMade


class TestPyfzf(unittest.TestCase):
    def setUp(self):
        fileloader = FileLoader()
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../../fzfaws/fzfaws.yml"
        )
        fileloader.load_config_file(config_path=config_path)
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput
        self.fzf = Pyfzf()

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_constructor(self):
        self.assertRegex(
            self.fzf.fzf_path,
            r".*/fzfaws.*/libs/fzf-[0-9]\.[0-9]+\.[0-9]-(linux|darwin)_(386|amd64)",
        )
        self.assertEqual("", self.fzf.fzf_string)

    def test_append_fzf(self):
        self.fzf.fzf_string = ""
        self.fzf.append_fzf("hello\n")
        self.fzf.append_fzf("world\n")
        self.assertEqual("hello\nworld\n", self.fzf.fzf_string)

    def test_construct_fzf_command(self):
        cmd_list = self.fzf._construct_fzf_cmd()
        self.assertEqual(
            cmd_list[1:],
            [
                "--ansi",
                "--expect=ctrl-c",
                "--color=dark",
                "--color=fg:-1,bg:-1,hl:#c678dd,fg+:#ffffff,bg+:-1,hl+:#c678dd",
                "--color=info:#98c379,prompt:#61afef,pointer:#e06c75,marker:#e5c07b,spinner:#61afef,header:#61afef",
                "--height",
                "100%",
                "--layout=reverse",
                "--border",
                "--cycle",
                "--bind=alt-a:toggle-all,alt-j:jump,alt-0:top,alt-s:toggle-sort",
            ],
        )

    @patch.object(subprocess, "Popen")
    @patch.object(subprocess, "check_output")
    def test_execute_fzf(self, mocked_output, mocked_popen):
        mocked_output.return_value = b"hello"
        result = self.fzf.execute_fzf(print_col=1)
        self.assertEqual(result, "hello")
        mocked_output.assert_called_once()

        mocked_output.return_value = b""
        self.assertRaises(NoSelectionMade, self.fzf.execute_fzf)

        mocked_output.return_value = b""
        result = self.fzf.execute_fzf(empty_allow=True)
        self.assertEqual("", result)

        mocked_output.return_value = b"hello"
        result = self.fzf.execute_fzf(multi_select=True, print_col=1)
        self.assertEqual(result, ["hello"])

        mocked_output.return_value = b"hello\nworld"
        result = self.fzf.execute_fzf(multi_select=True, print_col=1)
        self.assertEqual(result, ["hello", "world"])

    @patch.object(subprocess, "Popen")
    @patch.object(subprocess, "check_output")
    def test_check_ctrl_c(self, mocked_output, mocked_popen):
        mocked_output.return_value = b"ctrl-c"
        self.assertRaises(KeyboardInterrupt, self.fzf.execute_fzf)
        mocked_output.return_value = b"hello world"
        try:
            result = self.fzf.execute_fzf()
            self.assertEqual(result, "world")
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

        self.fzf.fzf_string = ""
        self.fzf.process_list([], "123", "asfasd", "bbbb", empty_allow=True)

        test_list = [{"foo": 1, "boo": 2}, {"foo": "b"}]
        self.fzf.process_list(test_list, "foo")
        self.assertEqual(self.fzf.fzf_string, "foo: 1\nfoo: b\n")

        self.fzf.fzf_string = ""
        self.fzf.process_list(test_list, "boo")
        self.assertEqual(self.fzf.fzf_string, "boo: 2\nboo: None\n")

        self.fzf.fzf_string = ""
        self.fzf.process_list(test_list, "www")
        self.assertEqual(self.fzf.fzf_string, "www: None\nwww: None\n")

        self.fzf.fzf_string = ""
        self.fzf.process_list(test_list, "foo", "boo")
        self.assertEqual(self.fzf.fzf_string, "foo: 1 | boo: 2\nfoo: b | boo: None\n")

    @patch.object(Pyfzf, "execute_fzf")
    def test_format_selected_to_dict(self, mocked_execute):
        mocked_execute.return_value = "foo: 1 | boo: 2 | wtf: None"
        result = str(self.fzf.execute_fzf(print_col=0))
        result = self.fzf.format_selected_to_dict(result)
        self.assertEqual(result, {"boo": "2", "foo": "1", "wtf": None})
