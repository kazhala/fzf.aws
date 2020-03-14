"""Cloudformation class to interact with boto3 cloudformation client

Main reason to create a class is to handle different account profile usage
and different region, so that all initialization of boto3.client could happen
in a centralized place
"""
import boto3
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.util import search_dict_in_list


class Cloudformation:
    """Cloudformation class to interact with boto3.client('cloudformaiton')


    """

    def __init__(self, region=None, profile=None):
        self.client = boto3.client('cloudformation')
        self.stack_name = None
        self.stack_details = None

    def get_stack(self):
        response = self.client.describe_stacks()
        fzf = Pyfzf()
        self.stack_name = fzf.process_list(
            response['Stacks'], 'StackName', 'StackStatus', 'Description', empty_allow=False)
        self.stack_details = search_dict_in_list(
            self.stack_name, response['Stacks'], 'StackName')

    def wait(self, waiter_name, delay=15, attempts=240):
        waiter = self.client.get_waiter(waiter_name)
        print(80*'-')
        waiter.wait(
            StackName=self.stack_name,
            WaiterConfig={
                'Delay': delay,
                'MaxAttempts': attempts
            }
        )

    def execute_with_capabilities(self, args, cloudformation_action, **kwargs):
        """execute the cloudformation_action with capabilities handled

        Args:
            args: argparse args
            cloudformation_action: function, the cloudformation method to execute
            **kwargs: key ward args to use in the cloudformation_action
            example:
                instance.execute_with_capabilities(args, instance.client.update_stack, StackName=stack_name)
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
                    **kwargs, Capabilities=self.get_capabilities())
        except self.client.exceptions.InsufficientCapabilitiesException as e:
            response = cloudformation_action(
                **kwargs, Capabilities=self.get_capabilities())
        return response

    def get_capabilities(self):
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
