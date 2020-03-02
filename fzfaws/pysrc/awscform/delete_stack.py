# delete stack operation
import boto3
from pysrc.util import get_confirmation, remove_dict_from_list
from pysrc.fzf_py import fzf_py

cloudformation = boto3.client('cloudformation')


def delete_stack(stack_name, stack_details):
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
        resource_list = response['StackResourceSummaries']
        # init fzf
        resource_fzf = fzf_py()
        # conitnue to pop fzf for user to select resource to retain
        while True:
            # prepare fzf string
            for resource in resource_list:
                resource_fzf.append_fzf(
                    f"ResourceLogicalId: {resource['LogicalResourceId']}")
                resource_fzf.append_fzf(2*' ')
                resource_fzf.append_fzf(
                    f"ResourceType: {resource['ResourceType']}")
                resource_fzf.append_fzf(2*' ')
                resource_fzf.append_fzf(
                    f"PhysicalId: {resource['PhysicalResourceId']}")
                resource_fzf.append_fzf('\n')
            # get selected id
            selected_id = resource_fzf.execute_fzf(empty_allow=True)
            if not selected_id:
                break
            logical_id_list.append(selected_id)
            # remove the selected entry
            resource_list = remove_dict_from_list(
                selected_id, resource_list, 'LogicalResourceId')
            if len(resource_list) < 1:
                break
            # clear fzf_string
            resource_fzf.fzf_string = ''
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
    print(response)
