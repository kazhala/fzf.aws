import io
import sys
import unittest
from unittest.mock import patch
from fzfaws.lambdaf.main import lambdaf


class TestLambdafMain(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_help(self):
        self.assertRaises(SystemExit, lambdaf, ["-h"])
        self.assertRegex(self.capturedOutput.getvalue(), r"usage: fzfaws lambda \[-h\]")

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        self.assertRaises(SystemExit, lambdaf, ["invoke", "-h"])
        self.assertRegex(
            self.capturedOutput.getvalue(), r"usage: fzfaws lambda invoke \[-h\]"
        )

        self.assertRaises(SystemExit, lambdaf, [])

    @patch("fzfaws.lambdaf.main.invoke_function")
    def test_invoke(self, mocked_lambdaf):
        lambdaf(["invoke", "--all", "--async"])
        mocked_lambdaf.assert_called_once_with(False, False, True, True, False, False)

        mocked_lambdaf.reset_mock()
        lambdaf(["invoke", "--payload", "./test.json"])
        mocked_lambdaf.assert_called_once_with(
            False, False, False, False, "./test.json", False
        )
