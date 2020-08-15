from fzfaws.cloudformation.helper import get_stack_name
import unittest
from unittest.mock import patch
from fzfaws.utils import StackNameValidator, prompt_style


class TestCloudformationHelper(unittest.TestCase):
    @patch("fzfaws.cloudformation.helper.prompt")
    def test_get_stack_name(self, mocked_prompt):
        mocked_prompt.return_value = {"answer": "hello"}
        result = get_stack_name()
        self.assertEqual(result, "hello")
        mocked_prompt.assert_called_with(
            [
                {
                    "type": "input",
                    "name": "answer",
                    "message": "StackName",
                    "validate": StackNameValidator,
                }
            ],
            style=prompt_style,
        )

        result = get_stack_name(message="hello")
        mocked_prompt.assert_called_with(
            [
                {
                    "type": "input",
                    "name": "answer",
                    "message": "hello",
                    "validate": StackNameValidator,
                }
            ],
            style=prompt_style,
        )

        mocked_prompt.return_value = {}
        self.assertRaises(KeyboardInterrupt, get_stack_name)
