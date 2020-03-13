# use fzf to allow user to select/acknowledge the capabilities
from pyfaws.pyfzf import PyFzf


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
