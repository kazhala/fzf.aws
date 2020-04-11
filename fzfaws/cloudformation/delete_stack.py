"""cloudformation delete stack operation

delete operations on the selected cloudformation stack
"""
import json
from fzfaws.utils.util import get_confirmation, remove_dict_from_list
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.cloudformation.cloudformation import Cloudformation


def delete_stack(profile=False, region=False, wait=False):
    """handle deltion of the stack

    Two situation, normal deletion and retained deletion.
    When the selected stack is already in a 'DELETE_FAILED' state, extra
    fzf operation would be triggered for user to select logical id to retain
    in order for deletion to be success.

    Args:
        profile: string or bool, use a different profile for this operation
        region: string or bool, use a different region for this operation
        wait: bool, pause the function and wait for stack delete complete
    Returns:
        None
    Raises:
        NoSelectionMade: whent he required fzf selection received zero selection
    """

    cloudformation = Cloudformation(profile, region)
    cloudformation.set_stack()

    logical_id_list = []
    if cloudformation.stack_details['StackStatus'] == 'DELETE_FAILED':
        print(
            'The stack is in the failed state, specify any resource to skip during deletion')
        logical_id_list = cloudformation.get_stack_resources()

    if not get_confirmation(
            f"Are you sure you want to delete the stack '{cloudformation.stack_name}'?"):
        exit()
    if len(logical_id_list) > 0:
        response = cloudformation.client.delete_stack(
            StackName=cloudformation.stack_name, RetainResources=logical_id_list)
    else:
        response = cloudformation.client.delete_stack(
            StackName=cloudformation.stack_name)
    print('Stack deletion initiated')

    # wait for completion
    if wait:
        cloudformation.wait('stack_delete_complete',
                            'Wating for stack to be deleted..')
        print('Stack deleted')
