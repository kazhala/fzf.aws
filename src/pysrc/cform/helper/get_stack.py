import boto3
from pysrc.pyfzf import PyFzf
from pysrc.util import search_dict_in_list

cloudformation = boto3.client('cloudformation')


def get_stack():
    # get all the stacks in the default region
    response = cloudformation.describe_stacks()
    stack_fzf = PyFzf()
    for stack in response['Stacks']:
        stack_fzf.append_fzf(f"Name: {stack['StackName']}")
        stack_fzf.append_fzf(2*' ')
        stack_fzf.append_fzf(f"Status: {stack['StackStatus']}")
        stack_fzf.append_fzf(2*' ')
        stack_fzf.append_fzf(f"Description: {stack['Description']}")
        stack_fzf.append_fzf('\n')
    selected_stack = stack_fzf.execute_fzf()
    # get the selected stack details
    stack_details = search_dict_in_list(
        selected_stack, response['Stacks'], 'StackName')
    return {'StackName': selected_stack, 'StackDetails': stack_details}
