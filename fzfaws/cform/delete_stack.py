"""cloudformation delete stack operation

delete operations on the selected cloudformation stack
"""
import json
from fzfaws.utils.util import get_confirmation, remove_dict_from_list
from fzfaws.utils.pyfzf import Pyfzf


def delete_stack(args, cloudformation):
    """handle deltion of the stack

    Two situation, normal deletion and retained deletion.
    When the selected stack is already in a 'DELETE_FAILED' state, extra
    fzf operation would be triggered for user to select logical id to retain
    in order for deletion to be success.

    Args:
        args: argparse args
        cloudformation: instance of the Cloudformation class
    Returns:
        None
    """

    logical_id_list = []
    if cloudformation.stack_details['StackStatus'] == 'DELETE_FAILED':
        print(
            'The stack is in the failed state, specify any resource to skip during deletion')
        response = cloudformation.client.list_stack_resources(
            StackName=cloudformation.stack_name)
        # copy the list
        response_list = response['StackResourceSummaries']
        fzf = Pyfzf()
        logical_id_list = fzf.process_list(
            response_list, 'LogicalResourceId', 'ResourceType', 'PhysicalResourceId', multi_select=True)

    confirm = get_confirmation(
        f"Are you sure you want to delete the stack '{cloudformation.stack_name}'?(y/n): ")
    if confirm == 'n':
        exit()
    if len(logical_id_list) > 0:
        response = cloudformation.client.delete_stack(
            StackName=cloudformation.stack_name, RetainResources=logical_id_list)
    else:
        response = cloudformation.client.delete_stack(
            StackName=cloudformation.stack_name)
    print('Stack deletion initiated')

    # wait for completion
    if args.wait:
        waiter = cloudformation.client.get_waiter('stack_delete_complete')
        print('--------------------------------------------------------------------------------')
        print("Waiting for stack to be deleted...")
        waiter.wait(
            StackName=cloudformation.stack_name,
            WaiterConfig={
                'Delay': 30,
                'MaxAttempts': 120
            }
        )
        print('Stack deleted')
