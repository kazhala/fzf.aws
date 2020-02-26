import boto3
from faws_py.util import get_confirmation, remove_dict_from_list
from faws_py.fzf_py import fzf_py

cloudformation = boto3.client('cloudformation')


def delete_stack(stack_name, stack_details):
    logical_id_list = []
    if stack_details['StackStatus'] == 'DELETE_FAILED':
        print(
            'The stack is in the failed state, specify any resource to skip during deletion')
        response = cloudformation.list_stack_resources(
            StackName=stack_name)
        resource_list = response['StackResourceSummaries']
        resource_fzf = fzf_py()
        while True:
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
            selected_id = resource_fzf.execute_fzf(empty_allow=True)
            if not selected_id:
                break
            logical_id_list.append(selected_id)
            resource_list = remove_dict_from_list(
                selected_id, resource_list, 'LogicalResourceId')
            if len(resource_list) < 1:
                break
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
