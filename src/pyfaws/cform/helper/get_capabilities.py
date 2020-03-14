# use fzf to allow user to select/acknowledge the capabilities
import boto3
from pyfaws.pyfzf import PyFzf

cloudformation = boto3.client('cloudformation')


def get_capabilities():
    fzf = PyFzf()
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
