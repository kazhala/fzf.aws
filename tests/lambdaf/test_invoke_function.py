import io
from pathlib import Path
import sys
import unittest
from unittest.mock import ANY, patch
from fzfaws.lambdaf.invoke_function import (
    invoke_function,
    invoke_function_sync,
    invoke_function_async,
)


class TestLambdafInvoke(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch("fzfaws.lambdaf.invoke_function.Pyfzf")
    @patch("fzfaws.lambdaf.invoke_function.invoke_function_async")
    @patch("fzfaws.lambdaf.invoke_function.invoke_function_sync")
    @patch("fzfaws.lambdaf.invoke_function.Lambdaf")
    def test_invoke_function(self, MockedLambdaf, mocked_sync, mocked_async, MockedFZF):
        lambdaf = MockedLambdaf.return_value
        invoke_function(all_version=True)
        lambdaf.set_lambdaf.assert_called_once_with(
            header="select function to invoke", all_version=True
        )
        mocked_sync.assert_called_once()
        mocked_async.assert_not_called()

        invoke_function(all_version=True, profile=True, region="us-east-2")
        MockedLambdaf.assert_called_with(True, "us-east-2")

        lambdaf.set_lambdaf.reset_mock()
        mocked_sync.reset_mock()
        invoke_function(all_version=True, asynk=True)
        lambdaf.set_lambdaf.assert_called_once_with(
            header="select function to invoke", all_version=True
        )
        mocked_sync.assert_not_called()
        mocked_async.assert_called_once()

        mocked_sync.reset_mock()
        fzf = MockedFZF.return_value
        invoke_function(payload=True, root=True)
        fzf.get_local_file.assert_called_once_with(
            json=True, header="select a json file as payload", search_from_root=True
        )
        mocked_sync.assert_called_once()

        mocked_sync.reset_mock()
        fzf.get_local_file.reset_mock()
        invoke_function(payload="./test.json", root=True)
        fzf.get_local_file.assert_not_called()
        mocked_sync.assert_called_once_with(lambdaf, "./test.json")

    @patch("fzfaws.lambdaf.invoke_function.base64")
    @patch("fzfaws.lambdaf.invoke_function.json")
    @patch("fzfaws.lambdaf.invoke_function.Lambdaf")
    def test_invoke_function_sync(self, MockedLambdaf, mocked_json, mocked_base64):
        lambdaf = MockedLambdaf.return_value
        lambdaf.function_detail = {
            "FunctionName": "testing",
            "Runtime": "python3.8",
            "Version": "$LATEST",
            "Description": None,
        }
        invoke_function_sync(lambdaf)
        mocked_json.loads.assert_called_once()
        mocked_base64.b64decode.assert_called_once()
        lambdaf.client.invoke.assert_called_once_with(
            FunctionName="testing", InvocationType="RequestResponse", LogType="Tail"
        )

        lambdaf.client.invoke.reset_mock()
        lambdaf.function_detail = {
            "FunctionName": "testing",
            "Runtime": "python3.8",
            "Version": "1",
            "Description": None,
        }
        invoke_function_sync(lambdaf)
        lambdaf.client.invoke.assert_called_once_with(
            FunctionName="testing:1", InvocationType="RequestResponse", LogType="Tail"
        )

        lambdaf.client.invoke.reset_mock()
        invoke_function_sync(
            lambdaf,
            payload_path=str(
                Path(__file__).resolve().parent.joinpath("../data/ec2_az.json")
            ),
        )
        lambdaf.client.invoke.assert_called_once_with(
            FunctionName="testing:1",
            InvocationType="RequestResponse",
            LogType="Tail",
            Payload=ANY,
        )

    @patch("fzfaws.lambdaf.invoke_function.Lambdaf")
    def test_invoke_function_async(self, MockedLambdaf):
        lambdaf = MockedLambdaf.return_value
        lambdaf.function_detail = {
            "FunctionName": "testing",
            "Runtime": "python3.8",
            "Version": "$LATEST",
            "Description": None,
        }
        invoke_function_async(lambdaf)
        lambdaf.client.invoke.assert_called_once_with(
            FunctionName="testing", InvocationType="Event", LogType="Tail"
        )

        lambdaf.client.invoke.reset_mock()
        lambdaf.function_detail = {
            "FunctionName": "testing",
            "Runtime": "python3.8",
            "Version": "5",
            "Description": None,
        }
        invoke_function_async(lambdaf)
        lambdaf.client.invoke.assert_called_once_with(
            FunctionName="testing:5", InvocationType="Event", LogType="Tail"
        )

        lambdaf.client.invoke.reset_mock()
        invoke_function_async(
            lambdaf,
            payload_path=str(
                Path(__file__).resolve().parent.joinpath("../data/ec2_az.json")
            ),
        )
        lambdaf.client.invoke.assert_called_once_with(
            FunctionName="testing:5",
            InvocationType="Event",
            LogType="Tail",
            Payload=ANY,
        )
