from fzfaws.utils import StackNameValidator, prompt_style
from PyInquirer import prompt


def get_stack_name(message="StackName") -> str:
    """Get user to input the stack name."""
    questions = [
        {
            "type": "input",
            "name": "answer",
            "message": message,
            "validate": StackNameValidator,
        }
    ]
    result = prompt(questions, style=prompt_style)
    if not result:
        raise KeyboardInterrupt
    return result.get("answer", "")
