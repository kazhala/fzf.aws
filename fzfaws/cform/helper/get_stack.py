"""get the stack

let user select a stack
"""
import boto3
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.util import search_dict_in_list

cloudformation = boto3.client('cloudformation')


def get_stack():
    """get the selcted stack"""
    response = cloudformation.describe_stacks()
    fzf = Pyfzf()
    selected_stack = fzf.process_list(
        response['Stacks'], 'StackName', 'StackStatus', 'Description')
    # get the selected stack details
    stack_details = search_dict_in_list(
        selected_stack, response['Stacks'], 'StackName')
    return {'StackName': selected_stack, 'StackDetails': stack_details}
