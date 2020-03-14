"""include capabilties during stack operations

use fzf to allow user ot selelct/acknowledge the capabilties
"""
import boto3
from fzfaws.utils.pyfzf import Pyfzf

cloudformation = boto3.client('cloudformation')


def get_capabilities():
    """display help message and let user select capabilities"""
    fzf = Pyfzf()
    fzf.append_fzf('CAPABILITY_IAM\n')
    fzf.append_fzf('CAPABILITY_NAMED_IAM\n')
    fzf.append_fzf('CAPABILITY_AUTO_EXPAND')
    print(80*'-')
    print('Some of the resources in your template require capabilities')
    print('Template macros, nested stacks and iam roles/policies would require explicit acknowledgement')
    print('More information: https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_CreateStack.html')
    print('Please select the capabilities to acknowledge and proceed (press tab to multi select)')
    return fzf.execute_fzf(empty_allow=True, print_col=1, multi_select=True)


def cloudformation_with_capabilities(args, cloudformation_action, **kwargs):
    """execute the cloudformation_action with capabilities handled

    Args:
        args: argparse args
        cloudformation_action: function, the cloudformation method to execute
        **kwargs: key ward args to use in the cloudformation_action
        example:
            cloudformation_with_capabilities(args, cloudformation.update_stack, StackName=stack_name)
    Returns:
        the raw response from boto3
    Exceptions:
       InsufficientCapabilitiesException: when the stack action require extra acknowledgement
    """
    try:
        if not args.capabilities:
            response = cloudformation_action(**kwargs)
        else:
            response = cloudformation_action(
                **kwargs, Capabilities=get_capabilities())
    except cloudformation.exceptions.InsufficientCapabilitiesException as e:
        response = cloudformation_action(
            **kwargs, Capabilities=get_capabilities())
    return response
