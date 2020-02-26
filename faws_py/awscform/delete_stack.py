import boto3
from faws_py.util import get_confirmation

cloudformation = boto3.client('cloudformation')


def delete_stack(stack_name):
    confirm = get_confirmation(
        f"Are you sure you want to delete the stack '{stack_name}'(y/n): ")
    if confirm == 'n':
        exit()
    else:
        response = cloudformation.delete_stack(StackName=stack_name)
        print(response)
