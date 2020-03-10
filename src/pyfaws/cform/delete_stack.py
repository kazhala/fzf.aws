# delete stack operation
import boto3
import json
from pyfaws.util import get_confirmation, remove_dict_from_list
from pyfaws.pyfzf import PyFzf
from pyfaws.cform.helper.process_template import process_list_fzf

cloudformation = boto3.client('cloudformation')


def delete_stack(args, stack_name, stack_details):
    # contains retained resource id if status is 'DELETE_FAILED'
    # only 'DELETE_FAILED' state would allow user custom retain resource during deletion
    # otherwise, retain policy would be read from template
    logical_id_list = []
    if stack_details['StackStatus'] == 'DELETE_FAILED':
        print(
            'The stack is in the failed state, specify any resource to skip during deletion')
        response = cloudformation.list_stack_resources(
            StackName=stack_name)
        # copy the list
        response_list = response['StackResourceSummaries']
        logical_id_list = process_list_fzf(
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
    response.pop('ResponseMetadata', None)
    print(json.dumps(response, indent=4, default=str))
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
