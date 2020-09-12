import json
from fzfaws.utils.pyfzf import Pyfzf
import io
import sys
from pathlib import Path
import unittest
from unittest.mock import ANY, patch
from fzfaws.lambdaf import Lambdaf
from fzfaws.utils import FileLoader
from botocore.paginate import Paginator


class TestLambdaf(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput
        config_path = Path(__file__).resolve().parent.joinpath("../data/fzfaws.yml")
        fileloader = FileLoader()
        fileloader.load_config_file(config_path=str(config_path))
        self.lambdaf = Lambdaf()

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_constructor(self):
        self.assertEqual(self.lambdaf.profile, "default")
        self.assertEqual(self.lambdaf.region, "us-east-1")
        self.assertEqual(self.lambdaf.function_name, "")
        self.assertEqual(self.lambdaf.function_detail, {})

        lambdaf = Lambdaf(profile="master", region="us-east-1")
        self.assertEqual(lambdaf.profile, "master")
        self.assertEqual(lambdaf.region, "us-east-1")
        self.assertEqual(lambdaf.function_name, "")
        self.assertEqual(lambdaf.function_detail, {})

    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Paginator, "paginate")
    def test_set_lambdaf(self, mocked_pagiantor, mocked_execute):
        data = Path(__file__).resolve().parent.joinpath("../data/lambda_function.json")
        with data.open("r") as file:
            mocked_pagiantor.return_value = json.load(file)
        mocked_execute.return_value = "FunctionName: testing | Runtime: python3.8 | Version: $LATEST | Description: None"
        self.lambdaf.set_lambdaf()
        mocked_execute.assert_called_once_with(header="", print_col=0)
        mocked_pagiantor.assert_called_once()
        self.assertEqual(
            self.lambdaf.function_detail,
            {
                "FunctionName": "testing",
                "Runtime": "python3.8",
                "Version": "$LATEST",
                "Description": None,
            },
        )
        self.assertEqual(self.lambdaf.function_name, "testing")

        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        mocked_execute.reset_mock()
        mocked_pagiantor.reset_mock()
        self.lambdaf.set_lambdaf(no_progress=True, header="hello", all_version=True)
        mocked_execute.assert_called_once_with(header="hello", print_col=0)
        mocked_pagiantor.assert_called_once_with(ANY, FunctionVersion="ALL")
