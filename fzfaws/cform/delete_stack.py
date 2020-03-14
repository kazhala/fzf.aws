"""cloudformation delete stack operation

delete operations on the selected cloudformation stack
"""
import boto3
import json
from fzfaws.utils.util import get_confirmation, remove_dict_from_list
from fzfaws.utils.pyfzf import Pyfzf

cloudformation = boto3.client('cloudformation')


def delete_stack(args, stack_name, stack_details):
    """handle deltion of the stack

    Two situation, normal deletion and retained deletion.
    When the selected stack is already in a 'DELETE_FAILED' state, extra
    fzf operation would be triggered for user to select logical id to retain
    in order for deletion to be success.

    Args:
        args: argparse args
        stack_name: string, name of the stack to update
        stack_details: dict, response from boto3
    Returns:
        None
    """

    logical_id_list = []
    if stack_details['StackStatus'] == 'DELETE_FAILED':
        print(
            'The stack is in the failed state, specify any resource to skip during deletion')
        response = cloudformation.list_stack_resources(
            StackName=stack_name)
        # copy the list
        response_list = response['StackResourceSummaries']
        fzf = Pyfzf()
        logical_id_list = fzf.process_list(
            response_list, 'LogicalResourceId', 'ResourceType', 'PhysicalResourceId', multi_select=True)

    confirm = get_confirmation(
        f"Are you sure you want to delete the stack '{stack_name}'?(y/n): ")
    if confirm == 'n':
        exit()
    if len(logical_id_list) > 0:
        response = cloudformation.delete_stack(
            StackName=stack_name, RetainResources=logical_id_list)
    else:
        response = cloudformation.delete_stack(
            StackName=stack_name)
    print('Stack deletion initiated')

    # wait for completion
    if args.wait:
        waiter = cloudformation.get_waiter('stack_delete_complete')
        print('--------------------------------------------------------------------------------')
        print("Waiting for stack to be deleted...")
        waiter.wait(
            StackName=stack_name,
            WaiterConfig={
                'Delay': 30,
                'MaxAttempts': 120
            }
        )
        print('Stack deleted')
